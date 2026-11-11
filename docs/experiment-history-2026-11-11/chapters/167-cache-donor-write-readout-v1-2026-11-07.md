# 167．DWR：同一供体写入端点到t2读取

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-11-07T11:52:34.013825+08:00；不能当作全部子运行起止。

**当时的目的与设计**

复用DWB的L11o/L11d，在t2的D直接读取、E旧预测修正和DE联合用途中交叉状态来源，获得和撤回都看完整自然答案。

**实际过程、结果与后来更正**

D获得0.396/0.271，撤回0.538/0.438；获得区间都跨0.25门槛，未过完整双向量级，撤回及自身恢复成立。5112完整轨迹含4176新反事实、792端点重放、144身份参照；首次schema预检失败和修复保留。

**来源身份**：`cache-donor-write-readout-v1-2026-11-07`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：DWR-01 v1：把供体写入接到后续状态使用

原路径：`docs/cache-donor-write-readout-plan-v1-2026-11-07.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-donor-write-readout-plan-v1-2026-11-07.zh-CN.md) · [单独阅读副本](../library/eae176b027920b8b.md)；SHA-256：`eae176b027920b8b53a176943c89519bb86fb9719529c46a2902b40394bd40da`。

---

#### DWR-01 v1：把供体写入接到后续状态使用

##### Material Passport

2026-11-07；Acupuncture缓存机制线；阶段：**下一阶段设计，未实现、未冻结、未运行**。依据DWB r02证据提交`c783cbdf92209712fb6ebb8a87620c708a8dd6ae`。本轮授权为论文、计划、自查和Git交付；不启动新GPU或模型调用。研究问题、已有结果与下一设计分开记载。

入口：[论文v1.4](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/mechanism-paper-skeleton-2026-11-05.zh-CN.md) · [证据缺口](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/mechanism-paper-evidence-gaps-2026-11-06.zh-CN.md) · [设计自查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-donor-write-readout-self-check-v1-2026-11-07.zh-CN.md) · [本轮旧记录元数据核对](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-donor-write-readout-input-audit-v1-2026-11-07.json)。

##### 1. 目的与论文增量

总问题不变：稀疏激活干预怎样改变历史信号、写入、旧状态处理和后续读取，最终造成大幅答案变化。

本轮问题：**DWB已经建立的纯局部供体写入，其形成的状态差，能否经t2直接读取D、旧预测修正E或二者联合，定向转移完整回答，并在反向替换后恢复自身选择？**

已有LVK→SRU回答的是同输入修复端点的读取关系；DWB回答的是历史来源经指定写入影响选择。两者的端点不同。此次使用DWB的同一对端点，补齐“历史来源→指定写入→后续状态使用→答案”的具体接口。预期增量是同端点、具有答案方向的计算联系，不是公式验证或重复定位热点。

本轮不以D必须胜过E为成功前提。D、E或联合有效都能给出新的计算解释；只有失分而无供体转移，也不算内容传递成功。已有DWB结果不以本卡阳性为存续条件。

##### 2. 依据、反例与取舍

| 资产 | 实测/已知内容 | 本卡用途 |
|---|---|---|
| [DWB r02](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/REPORT.zh-CN.md) | L11d净转移0.635/0.465，纯局部写入有效；CSTd分叉 | 固定端点和两方向，不从其他背景挑最好看的结果 |
| [LVK](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-local-v-k-v1-2026-11-03/CONTRACT.zh-CN.md)、[SRU](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-state-read-use-v1-2026-11-03/CONTRACT.zh-CN.md) | 局部写入与t2状态用途已有定义和验收 | 复用写入及读取算子，不重新发明分解 |
| [NWC](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-write-confirm-v1-2026-11-05/REPORT.zh-CN.md) | 多个随机读取扰动也导致首列错误 | 主要终点必须包含供体相关转移；撤回只降分不等于路径成立 |
| [SPF更正](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-selection-precedence-v1-2026-11-06/REPORT.zh-CN.md) | 干净q/k重要，状态单换不足，N1210截断前提失败 | 不假设q/k无关，不把不可判写阴性，不搜未经证明的“第二来源” |
| [基础审计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-mechanism-known-basics-audit-2026-10-31.zh-CN.md) | 架构允许状态经读出影响输出；固定驱动公式不是行为预测 | 新增量只由完整自然回答决定 |
| [直接近邻](https://arxiv.org/html/2611.01909v1) | 已有状态/输出移植与查询构造；全注意力reader不同于GDN读出 | 不把本卡命名为首次检索机制，也不照搬16–18层作为唯一读层 |

**选择L11o/L11d，而不同时铺开OO/DO。** 两个L11端点共享原生受针预填及写入k去偏移，不整体恢复卷积缓冲；只改变t1影子v的历史来源。这直接承接DWB的纯局部结果和LVK操作。OO/DO在恢复缓冲背景已有较强结果，但同时跑两套端点会增加矩阵，本轮没有必要。如果L11读取不成立，不自动切到OO/DO救假设。

本卡沿用6场景48输入，属于开发性连接检验。两方向为N4146、N1210，分别判读；保留第二方向是因为既有CSTd显著分叉，不能只选主要方向来构造统一故事。

##### 3. 固定操作与时序

- 模型Qwen3.5-4B，revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`；沿用DWB的BF16/eager/torch核、两方向、校准和提示形成规则，原文件只读，合同落地时逐一hash固定。
- G={13,14,16,17,18,20,21,22,24,25,26,28,29,30}，同一时刻联合操作，不将14层计为独立重复。
- 对每个接收者r、同场景供体d，重建O=L11o(r)、F=L11d(r,d)。F是**接收者的运行**在t1采用供体V历史计算影子v，不是供体整条运行。两端点的S₁分别记S₁ᴼ、S₁ᶠ。
- t1为最后提示token；继续各接收端点自然产生的首token，在处理这个token的t2，仅替换指定输出用途的S₁来源。32-token总生成上限、停止规则和编号解析完全沿用DWB；不强制额外前缀，不删异常输入。
- 本轮已对DWB旧记录做CPU元数据核对：两方向各48个L11o、348个L11d均到达t2；每对首token与该接收者OO的首token相同。此项是已有记录的时序前提，不是新科学结果。重建若不一致，停止并排查工程/身份，不挑出一致子集继续。

在每层当前接收分支的q、k、α、β下：

D(S₁)=αS₁ᵀq；E(S₁)=−αβ(kᵀq)S₁ᵀk。

获得侧：O端点使用S₁ᶠ替代D和/或E中的S₁ᴼ。撤回侧：F端点使用S₁ᴼ替代D和/或E中的S₁ᶠ。

复用SRU的`read_use`运算顺序：只改当前层输出中的指定用途，**不将替代S₁写进持久缓存**；当前层S₂仍由该分支原状态和当前驱动自然更新。较低层补丁会改变高层输入、q/k/v/门控、后续KV与生成，不能说它们全固定。t2后彻底卸载钩子。D和E分开使用同一状态属于显式的用途反事实，不冒充自然轨迹；联合DE仍不是替换整个持久状态。

##### 4. 最小充分矩阵

| 端点与用途 | 目的 | 每方向轨迹 |
|---|---|---:|
| L11o，原样续写 | 自身选择参照；对不同供体可复用同一条输出 | 48 |
| L11d，原样续写 | 供体选择参照，对齐DWB | 348 |
| O接收，D读F | 直接读取是否获得供体选择 | 348 |
| O接收，E读F | 修正用途是否获得供体选择 | 348 |
| O接收，DE读F | 两种用途联合是否必要于这项操作效果 | 348 |
| F接收，D读O | 撤回直接读取来源后的选择 | 348 |
| F接收，E读O | 撤回修正用途来源后的选择 | 348 |
| F接收，DE读O | 联合撤回后的选择 | 348 |

每方向2484条，两个方向4968条完整轨迹，其中4176条是新读取反事实、792条为端点重放。供体类型沿用AL84、KS96、RS84、BD84，不额外添加异场景供体。另有C0与L00身份参照144条完整回答。零钩子等工程前向不伪装为新独立样本。

完整配对必须保留：D_tr对照集合依赖其他供体，不能只抽AL冲突条目却沿用原统计量。主科学单位仍为6场景；348配对和多臂不能变成348或几千个独立样本。

##### 5. 估计对象、判据与所有结局

主读数采用SPF/DWB的冻结D_tr与原解析器；固定答首列、自身或停止等供体无关输出的净值为零。对j∈{D,E,DE}定义：

- Gⱼ = D_tr(O读F，j) − D_tr(O)：获得侧净供体转移。
- Wⱼ = D_tr(F) − D_tr(F读O，j)：撤回侧净转移下降。
- Rⱼ：AL/BD的168个冲突配对中，F读O相对F的自身答案比例提升；必须逐配对报告。
- Vⱼ：各臂有效单编号完整回答比例；停止、截断、首列错号、自身与供体对应的输出另列，不能将全部未答对合成一种。

重抽沿用6场景、10000次、固定种子20261106；同一抽样索引用于所有配对差，场景符号置换p只作开发性描述。报告所有臂及区间，不挑最优臂重新定义主假设。D为首要预登记读取比较，E与DE为必须同时报告的计算比较；不能因为三者之一p<0.05便声称确认。此面板不承担独立总体显著性证明。

**量级与前提。** 继承DWB的最小关注量M=0.25，不用本轮结果调门槛。区间下界≥M为达到量级，上界<M为低于量级，其余不可判；若上下界都恰等于M，单列边界不可判。达到量级不等同于解释25%机制。量级较小但区间为正的效应仍报告，不称严格无效。

端点F须重现DWB原输出及冻结转移，O亦须逐token对应原L11o。主要比较有效完整回答比例须≥0.90，且相对其接收端点下降≤0.05（分母为全部348有序配对；O按相同配对展开）。阈值是预设交付护栏，不是等效检验。完整回答不足时保留输出，将相应解释标为交付混淆，不增token预算救结果。

| 观察组合（各用途、各方向分别判） | 允许的认识 | 下一步 |
|---|---|---|
| G达到M、W达到M，交付护栏过，R区间下界>0 | 该用途替换可获得并撤回供体选择，且撤回朝自身恢复；支持同端点双向连接 | 将实际支持用途加入正文，随后冻结关系准备独立材料确认 |
| G达到M，W不足/不可判 | 该用途在O背景足以传递选择；未证明反向依赖 | 保留获得侧贡献，不称必要路径；不自动加层 |
| W达到M，G不足，且R提升 | 改变该用途可恢复自身选择，但未建立供体选择的获得联系 | 不把恢复等同于完整内容路径；保留已有写入结果 |
| W下降但R不提升、或交付护栏失败 | 可能是一般扰动/交付退化；不能称选择被成功撤回 | 记录混淆，当前强解释不成立 |
| 仅DE双向成立 | 两用途的联合操作支持连接，单用途不足 | 写联合贡献；不能命名D唯一或E无用 |
| D、E都成立 | 两种用途均有可操作作用 | 不强行选一个“真正机制”，不把效应相加当份额 |
| G或W异号 | 相应替换与预期方向相反 | 撤回该方向的原预测，保留异号与完整回答 |
| 全部低于M/不可判 | 当前指定t2用途不能提供所需量级的桥接/证据不足 | 本卡收尾；不续扫层、时刻、剂量、模型找阳性 |
| 重建/零钩子/范围校验失败 | 工程失败，科学结论尚未测到 | 中止；记录偏离，不将失败算阴性 |

“D比E更强”仅在对应G/W的配对差区间也支持时作本设置下描述，不等于用途天然更重要。随机对照的旧结果保持有效：本卡不声称原生状态方向比任意随机方向特殊，也不证明供体信息必定是语义而非幅度相关差异。D_tr与供体标签置换检验的是来源关联，不能排除供体相关的一般幅度效应。因此不为恢复已被NWC否定的卖点另跑随机族；若下一篇主张需要“编码内容/方向优于范数”，须另行有匹配幅度的识别设计，不能从本卡顺带宣布。

##### 6. 实现和数值验收（待完成，不算设计自查结果）

1. 新实验目录独立版本，不改DWB/SRU冻结文件。直接复用DWB形成/写入和SRU读取函数；组合后仍需验收，不能只因旧函数通过就放行。
2. 固定源码、模型、tokenizer、校准、48输入、348配对/方向、原输出与冻结哈希；保存所有未通过检查和实际耗时。配对账本必须与DWB逐项一致。
3. CPU验证D_tr固定输出为零、全供体/自身/首列/停止等合成世界，以及上述各判读结局；方向分叉、缺失和截断不可被汇总掩盖。已有元数据核对只覆盖时序/计数，不称完整CPU验收。
4. 模型预检：一个固定接收者/场景、该接收者所有供体、两方向、全部臂；按照ID排序选首个，不能按现有效果选择。重建端点与DWB逐token及已有t2哈希对应，随后验证零用途补丁与未挂钩输出逐位一致。
5. 数值：SRU原顺序计算，FP64相对误差≤1e−5；DE输出与相同当前驱动下用供体S₁计算的局部参照比较。当前层持久S₂不使用替代S₁；钩子只在t2、只触及G、每层一次，t3起卸载；源缓存/权重不得被原地改动。
6. 正式全量都保留端点桥接和调用范围检查，不用预检代替正式。运行器、统计、冻结、预检和执行授权分别登记。

##### 7. 资源与停止边界

已用旧数据完成端点首token/到达t2的核对；现有原始文本不包含新用途替换的自然回答，公式也不能推出其行为，因此新读取臂最终需要模型运行。形成缓存/中间张量若仍在服务器可核hash后复用；资产缺失时所需重建必须入预算，不能借“只补一格”漏账。

正式科学部分4968条，加身份参照144条，共5112条完整轨迹；另计划最多792次零用途单步检查、144份C/T形成和936个t1端点前向。它们与5112条轨迹有阶段包含关系，不相加成样本数。可在同一端点缓存上分叉，避免为每个t2臂重复形成。FP64检查、模型加载、分支复制、保存、失败预检与工程重试均计入时间。

DWB正式3816条用1346.877秒，简单按完整轨迹外推5112条约0.50小时；读取钩子、长输出与重建开销不同，这不是本卡实测预测。**拟预留正式上限2.0 GPU进程小时；首次预检0.25小时，至多一次纯工程修复预检0.25小时，总上限2.5小时。** 预检后依据实际形成、各臂生成长度、读取开销和磁盘保存重新估计；预计超限则在正式前停止并报告，不能缩面板、删反例或提高上限来硬跑。当前没有上卡、排队或显存并行决策。

##### 8. 后续如何扩展贡献

本卡结束后优先整合实际结果。若连接成立，将其与已完成DWB写入反向臂组成完整证据，并用新材料检验预测；材料需解耦位置、实体和答案编号，不把模板换词冒充三者解耦。该确认的面板规模与功效需依据冻结效应、场景相关和目标精度单独设计，不能直接把24情境当作天然足够。

随后检验可比模型/任务上的关系，准备工作可提前，但新运行不自动授权。若连接未成立，写清哪些写入效应仍成立、哪个读取预测被否定，再围绕实际站住的贡献判断确认范围。不会将每次阴性都转成更小的局部定位项目，也不会为了保持宏大叙事隐去失败。

本卡通过的是[作者逻辑设计自查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-donor-write-readout-self-check-v1-2026-11-07.zh-CN.md)。实现、数值、资源实测和独立确认尚未完成；本轮到文稿与计划交付为止。

---

### 原件 2：DWR-01 v1：作者设计自查与反方修订记录

原路径：`docs/cache-donor-write-readout-self-check-v1-2026-11-07.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-donor-write-readout-self-check-v1-2026-11-07.zh-CN.md) · [单独阅读副本](../library/db460a628958b9de.md)；SHA-256：`db460a628958b9dee4317408640c1769d0cebad2b34f2b5f7d5f2f188d20bf85`。

---

#### DWR-01 v1：作者设计自查与反方修订记录

2026-11-07。对象：[DWR-01计划](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-donor-write-readout-plan-v1-2026-11-07.zh-CN.md)。规范：[experiment-design-self-check v1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/experiment-design-self-check.zh-CN.md)；已读[基础知识审计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-mechanism-known-basics-audit-2026-10-31.zh-CN.md)。同一助手完成，不称独立审查。结论：**逻辑设计通过；实现、数值验收、模型预检未完成；未运行、未冻结。**

##### 1. 设计卡与前后比较

- 主线：解释稀疏干预经历史、写入、状态处理与读取造成大幅答案变化。
- 本轮：DWB的L11o/L11d状态差是否经一次t2 D/E用途传递并撤回完整回答的供体选择。
- 增量：把“历史—写入—选择”与既有“写入—读取—回答”接到同一对端点，不能只重做状态交换或热图。
- 依据：DWB纯局部净转移两方向成立、旧SRU用途替换有行为作用；反例是NWC一般扰动、SPF状态单换失败、CSTd方向分叉。
- 操作/终点：计划§3–§5；原生受针预填、同一写入k操作、只改变影子v历史来源，t2替换输出用途，随后自由回答；D_tr、有效编号、冲突配对自身恢复分开。
- 范围：48已见输入、6场景、每方向348配对；两方向分别判；不是独立确认。
- 成本/停止：计划§7；旧数据优先，拟全轮2.5 GPU进程小时，未实测；不自动上卡，工程失败/量级不足/异号均有退出。

最近已完成DWB r02检验的是t1写入充分性、反向替换和受针状态可用性；本卡保持模型、输入、方向、写入端点和解析器，只补t2用途。此前讨论中的“先搜第二来源”和“注意力热图定位”不进入本卡：第二来源并未被识别，热图不能代替因果读取检验。9B和新材料保留在推广路径，不为本卡阳性预先计分。

##### 2. C01–C14逐项审查

| 项 | 判定与理由 | 对应位置 |
|---|---|---|
| C01 主线 | 通过：总问题不变；读取连接完成现有写入效应的解释接口，不将EOS/撤针作为总目标 | 计划§1/§8 |
| C02 增量 | 通过：同一供体写入状态的用途替换可把两个已有效关系接通；成功不只是输出变化，失败能撤回具体一次t2假说 | §1/§5 |
| C03 资产 | 通过：直接采用DWB、LVK、SRU与SPF的操作/统计；NWC反例限制解释；本轮核对已有首token和到达t2记录 | §2/§3及元数据JSON |
| C04 假设 | 通过：D、E、联合均可成立；状态作用分叉和随机退化是最不利证据；不预设信息删除或D独占 | §2/§5 |
| C05 操作 | 通过：明确r/d、L11o/d、14层、t1形成/t2输出用途/t3卸载；F是接收者带供体历史写入的端点，非供体整状态 | §3 |
| C06 路径 | 通过：仅当前层指定输出用途改变；本层S₂自然更新，高层驱动、KV、后续生成允许响应，不声称未来缓存固定 | §3/§6 |
| C07 耦合 | 通过：显式承认D/E分别换S是用途反事实；DE仍不是持久状态替换，q/k/门来自当前分支；不称原生唯一中介 | §3/§5 |
| C08 归因 | 通过：双向选择与自身恢复才能写同端点双向连接；仅获得侧只写条件充分；撤回失分不单独算路径；无机制比例 | §5 |
| C09 区分 | 通过：单用途、联合、异号、交付混淆均有不同判读；D/E可共存；零结果不自动指认KV或其他部位 | §5表 |
| C10 指标 | 通过：完整自然回答为主；D_tr固定首列为零，另列有效交付、截断和自身恢复；不以t1/t2 logits代替结果 | §4/§5 |
| C11 失败 | 通过：工程前提和科学判读分离；M为关注量级，零效应、低于M、不可判分开；不增token救N1210 | §5–§7 |
| C12 成本 | 通过：旧记录先核对；只用一对写入端点，六个新用途格，不同时加OO/DO；形成、桥接、预检失败均列预算 | §4/§7 |
| C13 可信度 | 通过：已见数据明确，6场景聚类；两方向不混池；所有臂与区间报告；代码/冻结待做，未冒充验收 | Passport、§5/§6 |
| C14 累积 | 通过：阳性接通主线后转独立确认；阴性保留DWB并停止本读取解释，不无限扫层；论文目标不随失败缩窄 | §1/§8 |

##### 3. 历史错误逐项处理

| 编号 | 本卡处理 |
|---|---|
| E01 | 总目标在计划首段保留；一次读取是补证接口，不重新定义课题 |
| E02 | 复用G14，不将16–18层当天然特殊读层；文献reader与本卡对象分开 |
| E03 | 不称少坐标等于小扰动；本卡不估计范数放大，不由方向转移宣称幅度机制 |
| E04 | D/E公式及局部恒等只作工具/验收；完整回答决定科学增量 |
| E05 | 共享q/k/门的来源明确，D/E分换承认反事实，不用value补偿假装自然 |
| E06 | 不把v或单用途称全部写入/处理；k去偏移条件保持一致 |
| E07 | 双向阳性仅支持指定反事实连接，不能推出原生唯一通路 |
| E08 | 所有来源按r/d与O/F逐一固定；不命名无条件直接/间接效应 |
| E09 | 不用两项变化或交互拼因果；真正操作同一写入形成的S₁用途 |
| E10 | 输出、有效编号、自身/供体、停止/截断各列；失分不替代交付 |
| E11 | D_tr是操作对比，不是信息存量；无效不称没有信息 |
| E12 | D_tr不自动消除供体相关损伤；增加完整回答和自身恢复判读；标签置换不当作所有随机扰动零分布 |
| E13 | F显式引入供体历史；不把供体答案称恢复接收者记忆 |
| E14 | 条件充分、反向依赖、形成来源和自然路径分开；恢复幅度不称解释率 |
| E15 | 直接使用DWB的L11o/d，不将旧SRU不同端点阳性移花接木 |
| E16 | 工程过后允许科学无效或异号；没有“阴性必有bug”流程 |
| E17 | 输出用途替换不撤销t1所有后果；不说其余运行回到了O |
| E18 | D/E阴性不把剩余解释命名为KV或浅层；不自动穷举 |
| E19 | 零钩子、局部DE恒等、逐token重放仅是工程验收 |
| E20 | D/E共用同一状态可同时有作用；联合有效也有价值 |
| E21 | 近邻定向核对，正常检索机制归于先行工作；新增是干预后的同端点计算连接 |
| E22 | 48输入/348配对/5112轨迹不冒充独立场景；不称新材料确认 |
| E23 | 自查非独立评审；计划通过不等于实现/冻结/运行 |
| E24 | 不要求本卡找到唯一信息载体或完整原生失效；同端点可定向传递是有价值的增量 |
| E25 | 删去第二来源搜寻、热图、两套背景全矩阵及全层扫描；每保留格都有判读用途 |
| E26 | t1形成差与t2输出用途分清；后续响应保留，估计条件总效果，不假装隔离全部自然中介 |

##### 4. 实质反方检查与修订

**质疑一：直接用OO/DO最强结果，会只证明恢复缓冲背景中的关系，正文又要补纯局部桥接。** 修订：本卡主端点直接用DWB已阳性的L11o/L11d，承接原生预填上的局部操作。代价是主要方向自身基线39/48而非全对；因此撤回看相对自身恢复，不假设每条都可恢复为正确。最终稿不再并行两套端点。

**质疑二：t1后首token不同，读取相同索引不是同一问题。** 处理：本轮核对既有原始记录，48个自身及348个供体端点/方向均到达t2，首token逐接收者一致。正式重建继续验证；不能仅据面板名称认定一致。无需新GPU来先看这个前提。

**质疑三：只做读取撤回，随机损伤也会使供体跟随下降。** 修订：双向比较并列，获得侧要产生净供体转移；撤回必须有效交付且自身恢复提升。只有W下降不写内容传递。这正面处理NWC反例。仍不能排除供体相关幅度效应，所以不承诺方向编码独占或语义已经解耦。

**质疑四：要求D单独成功，若E或联合才有效会再次把结果写窄。** 修订：预登记D、E、DE均有科学解释；主张关心状态使用怎样承接选择，联合也能推进机制。D为首要比较不意味着阴性后删除E；所有结果报告，开发性标签不包装成多重检验后的独立确认。

**质疑五：读出反事实产生补偿，不能证明自然路径。** 判断：这是支持范围而非当前承诺的硬伤。该反事实可直接检验同一写入状态差经哪个输出用途足以改变回答；自然必要路径不在承诺中，不能借一般patching风险否定所有可测计算关系。

**质疑六：下一卡再成功，仍只有六场景，论文会困在越来越细的格子。** 修订：本卡限定一个时刻、已有层集合、一对端点；收尾后按实际站住的关系做独立材料确认和可比模型/任务检验，不自动局部扫层。课题的广度目标明确保留。失败亦结束该单步解释，不继续变窄求阳性。

**质疑七：计划用了D_tr，却只保留AL供体会改变对照集合。** 修订：保留原348完整供体账本和统计源码，不为省算力只抽AL；全部轨迹计数重算为4968科学轨迹+144身份参照。两方向分开统计。

**质疑八：称G/W超过0.25为“机制确认”仍会夸大。** 修订：M明确是关注量级，场景重抽区间属于开发不确定性；6场景、多臂、已见数据限制保留。交付护栏只防明显混淆，不证明等效；刚好边界判不可判，低于量级不称严格零。

##### 5. 最终状态与复查

上述修订后重过C01/C02/C05–C10/C12–C14：仍回答原来的同端点读取连接，具有完整答案与来源方向增量；未靠删掉核心问题过关。没有已知逻辑硬伤留给用户审核。

已完成：读正式证据与近邻、核旧输出元数据、明确矩阵/判读/退出、作者反方自查。未完成：新运行器、CPU判读测试、跨模块数值验收、源资产就绪验证、实际预检与资源估计、冻结、正式运行。未来这些闸门完成前不能把逻辑通过写成“可以直接上卡”。本轮不运行模型。

---

### 原件 3：DWR-01 r01 执行合同

原路径：`experiments/cache-donor-write-readout-v1-2026-11-07/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/CONTRACT.zh-CN.md) · [单独阅读副本](../library/935a5c74716a3e3a.md)；SHA-256：`935a5c74716a3e3ac315ec27a24a1b1484779793c40cc464dc5174b2428a1a68`。

---

#### DWR-01 r01 执行合同

2026-11-07。执行依据为[已交付计划](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-donor-write-readout-plan-v1-2026-11-07.zh-CN.md)及[设计自查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-donor-write-readout-self-check-v1-2026-11-07.zh-CN.md)，两者的科学问题、端点、臂、门槛与退出分支不变。旧文件中的“未授权”记录的是交付当时状态，由本次明确授权更新，不追改历史。

##### 授权与边界

用户本次原话：“那就把运行器、CPU测试、数值验收和冻结都补齐，预检通过后直接上卡跑正式实验。显存够就并行，不够就排队，按计划预算执行，跑完分析结果、更新论文并推送 GitHub，再跟我汇报。”

允许本卡 CPU、首次预检、至多一次纯工程修复预检以及验收通过后的正式运行。授权不覆盖新材料、9B、额外层/时刻/剂量扫描。失败保留，不换端点救假设。预检/正式均保留每个端点与DWB逐token及t2 logits SHA桥接、每个O/F的零用途补丁逐位检查、来源缓存完整性、权重与钩子检查。

##### 固定实现

- `dwr_run.py`复用DWB形成、LVK `LHook/t1L`、SRU `RHook/read_use`，不修改旧冻结代码。两个方向、6场景48输入；每方向348完整有序配对。
- O=L11o，F=L11d；每对首token相同且非停止。t2使用各分支自然首token，G14联合D/E/DE用途替换；原生当前层S2保留。更高层输入和之后轨迹自然响应，不能称所有驱动固定。
- 4176新读取反事实+792端点重放+144 C0/L00身份参照=5112完整轨迹；936次t1前向、144份形成、792次零用途t2。自然生成沿用32-token及原解析器。原函数的`trajectories`计数排除首步停止，完整实验数以记录中`n_runs`为准。
- 正式场景原顺序按worker编号交错分配，最多两worker，各占一张可用GPU；显存需达到旧运行器下限及两倍本预检峰值。无空位就等待，不能终止其他项目。
- 预检每场景按接收者ID排序选第一名、其全部同场景供体、两个方向全臂。形成所有场景缓存计入开销；不按现有效果抽样。
- 冻结包括本卡代码、合同、自查、计划及旧依赖、旧参考记录哈希。授权和运行回执使用既有`exp.write`规范序列化，避免DWB旧轮授权字节不一致问题。

##### 统计与结局

D_tr、6场景bootstrap 10000次种子20261106、2000次供体标签置换与原解析器不变。G和W按接收者计算配对D_tr差；R为AL/BD冲突配对上的自身恢复**逐对差**，在场景层重抽，分母168/方向。R的点估计按配对加权，不将48个接收者等权代替168对比例。原始逐对变化保留。

M=.25；lo≥M达到量级，hi<M低于量级，其余不可判，lo=hi=M单列边界不可判。交付比例分母348/臂，须≥.90且相对接收端点下降≤.05。两侧达到量级并且R下界>0及交付通过才能判同端点双向连接；其余严格按计划§5分支报告。两方向、三用途、所有区间全部交付；D/E之差也做配对区间。不能用标签置换排除供体相关幅度效应。开发材料不冒充独立确认。

##### 数值与工程放行

CPU测试包含原SRU的torch原核零补丁逐位对齐、FP64误差≤1e-5、DE局部参照、返回S2为原生更新，以及实面板计数/并行分区、合成全供体/自身/固定输出、方向分叉、缺失拒收、截断解析与结局边界。CPU通过后冻结。上卡预检全臂验收后，按本预检的形成、续写、复制和保存时间外推正式；预计超过正式预算则不启动。

##### 资源

首次预检≤900 GPU进程秒；最多一次工程修复预检≤900；正式≤7200；总≤9000（2.5 GPU进程小时）。模型加载、身份校验、失败、保存、FP64与重建计入。正式双worker各至多3600秒，单worker至多7200；保守墙钟终止约束保证合计预算。只杀本卡worker。输出上限2 GiB/worker，不存大模型/缓存张量。任何工程修复另留失败目录、偏离说明和新冻结，不覆盖旧证据。

最终交付：运行源码与CPU记录、freeze/authorization/preflight/formal回执、全部原始回答、冻结分析、报告、论文及缺口同步、Git提交和远端核对。成功只表示协议内测量完成，不预设科学阳性。

---

### 原件 4：DWR-01 偏离索引

原路径：`experiments/cache-donor-write-readout-v1-2026-11-07/DEVIATIONS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/DEVIATIONS.zh-CN.md) · [单独阅读副本](../library/a9c1acfe4a769258.md)；SHA-256：`a9c1acfe4a769258277563cf3a59117254c6cf44858a4fcbceb273148047a296`。

---

#### DWR-01 偏离索引

冻结前开发：本地语法编译受macOS默认pycache路径沙箱限制，改用临时目录；未调用模型，不属科学偏离。CPU失败和修正以readiness记录为准，冻结前完成。模型预检/正式若失败另存编号说明，不追改已冻结本文件。

本轮科学矩阵、端点、统计判据及预算未变。R配对加权在执行合同中明确，是原计划“168配对自身答案比例提升”的直接实现。

---

### 原件 5：DWR-01：供体写入到后续读取的同端点检验

原路径：`experiments/cache-donor-write-readout-v1-2026-11-07/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/REPORT.zh-CN.md) · [单独阅读副本](../library/786bb5104f8923c8.md)；SHA-256：`786bb5104f8923c88cf805e7c830eda61fde56b3a9db5f682d455ce40eb16d5b`。

---

#### DWR-01：供体写入到后续读取的同端点检验

2026-11-07。正式运行与工程验收完成。科学结论按冻结判据逐方向、逐用途判读。

**结论：同一供体写入差异的直接读取已经测到正向获得和有自身恢复的撤回；撤回达到预设量级，获得侧量级仍不可判，因此没有通过完整双向门槛。** D与联合DE均为这一结局，E没有支持同样的选择传递。实验全部完成，不追加运行救门槛。

##### 1. 本轮测了什么

总问题仍是稀疏激活干预怎样改变历史信号、写入、状态使用及完整回答。本轮复用DWB的O=L11o与F=L11d端点：在同一受针接收者中，仅让t1指定写入采用自身或供体的V历史；再在t2仅改变D直接读取、E旧预测修正或联合DE输出用途的状态来源。获得侧O读F，撤回侧F读O。当前层持久S2保留原生更新，后续轨迹自然生成。

模型Qwen3.5-4B（revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`），两方向、6个已见开发场景48输入，每方向348有序配对；AL/BD选择冲突配对168。32-token自然生成，原冻结完整回答解析器不变。

##### 2. 完整结果

G=获得侧相对O的净供体转移增量；W=撤回相对F的净转移下降；R=168冲突配对的逐对自身答案恢复比例差。D_tr不是准确率或机制份额。区间为6场景聚类重抽95%区间；M=.25，全部臂报告，不挑选阳性。

| 方向 | 用途 | G | W | R | 冻结判读 |
|---|---|---:|---:|---:|---|
| N_L00_C4146_D-1 | D | 0.396 [0.196, 0.573] | 0.538 [0.319, 0.732] | 0.482 [0.244, 0.655] | self_recovery_without_gain |
| N_L00_C4146_D-1 | E | -0.010 [-0.031, 0.000] | -0.052 [-0.085, -0.016] | -0.024 [-0.042, -0.006] | opposite_direction |
| N_L00_C4146_D-1 | DE | 0.382 [0.186, 0.552] | 0.552 [0.337, 0.740] | 0.452 [0.215, 0.632] | self_recovery_without_gain |
| N_L00_C1210_D-1 | D | 0.271 [0.200, 0.340] | 0.438 [0.321, 0.587] | 0.476 [0.369, 0.560] | self_recovery_without_gain |
| N_L00_C1210_D-1 | E | 0.000 [0.000, 0.000] | -0.035 [-0.111, 0.010] | -0.006 [-0.018, 0.000] | below_margin |
| N_L00_C1210_D-1 | DE | 0.302 [0.214, 0.379] | 0.427 [0.301, 0.594] | 0.435 [0.351, 0.494] | self_recovery_without_gain |

冻结代码标签`self_recovery_without_gain`的含义是“撤回及自身恢复成立，**获得未达到确认所需的量级判据**”，不是获得效应为零。本轮D/DE的G区间均为正，但跨过M=.25，因此G_level是indeterminate，不能改称below或无效，也不能降低门槛后补记双向通过。六场景上的正区间仍是开发性读数。

###### 各臂完整回答与供体读数

| 方向 | 臂 | D_tr | 有效回答 | 自身 | 首列错号 | 其他错号 | 停止 | 其他 | 截断 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| N_L00_C4146_D-1 | L11o | 0.000 [0.000, 0.000] | 348/348 | 285 | 63 | 0 | 0 | 0 | 0 |
| N_L00_C4146_D-1 | L11d | 0.635 [0.431, 0.812] | 348/348 | 121 | 157 | 70 | 0 | 0 | 0 |
| N_L00_C4146_D-1 | gainD | 0.396 [0.196, 0.573] | 348/348 | 157 | 164 | 27 | 0 | 0 | 0 |
| N_L00_C4146_D-1 | gainE | -0.010 [-0.031, 0.000] | 348/348 | 306 | 42 | 0 | 0 | 0 | 0 |
| N_L00_C4146_D-1 | gainDE | 0.382 [0.186, 0.552] | 348/348 | 163 | 157 | 28 | 0 | 0 | 0 |
| N_L00_C4146_D-1 | withdrawD | 0.097 [0.052, 0.143] | 348/348 | 255 | 93 | 0 | 0 | 0 | 0 |
| N_L00_C4146_D-1 | withdrawE | 0.688 [0.480, 0.869] | 348/348 | 114 | 161 | 73 | 0 | 0 | 0 |
| N_L00_C4146_D-1 | withdrawDE | 0.083 [0.039, 0.131] | 348/348 | 247 | 101 | 0 | 0 | 0 | 0 |
| N_L00_C1210_D-1 | L11o | 0.000 [0.000, 0.000] | 348/348 | 348 | 0 | 0 | 0 | 0 | 0 |
| N_L00_C1210_D-1 | L11d | 0.465 [0.346, 0.604] | 348/348 | 212 | 112 | 24 | 0 | 0 | 0 |
| N_L00_C1210_D-1 | gainD | 0.271 [0.200, 0.340] | 348/348 | 236 | 104 | 8 | 0 | 0 | 0 |
| N_L00_C1210_D-1 | gainE | 0.000 [0.000, 0.000] | 348/348 | 348 | 0 | 0 | 0 | 0 | 0 |
| N_L00_C1210_D-1 | gainDE | 0.302 [0.214, 0.379] | 348/348 | 242 | 96 | 10 | 0 | 0 | 0 |
| N_L00_C1210_D-1 | withdrawD | 0.028 [0.007, 0.046] | 348/348 | 334 | 14 | 0 | 0 | 0 | 0 |
| N_L00_C1210_D-1 | withdrawE | 0.500 [0.373, 0.641] | 348/348 | 210 | 113 | 25 | 0 | 0 | 0 |
| N_L00_C1210_D-1 | withdrawDE | 0.038 [0.000, 0.078] | 348/348 | 324 | 24 | 0 | 0 | 0 | 0 |

L11o在表中为配对展开的348条读数，实际只重放48条/方向；不能把这些重复当新样本。所有供体类型的行/实体跟随、固定标签置换、逐冲突配对恢复变化均见机器可读判读。

###### D与E的配对比较

| 方向 | G_D−G_E | W_D−W_E |
|---|---:|---:|
| N_L00_C4146_D-1 | 0.406 [0.225, 0.573] | 0.590 [0.363, 0.787] |
| N_L00_C1210_D-1 | 0.271 [0.200, 0.340] | 0.472 [0.352, 0.619] |

本比较是所测操作下的描述；不能由D/E差异声称自然唯一用途、完整因果中介或机制份额。

##### 3. 对论文的实际增量与限制

**补上的部分。** 以前DWB测到“供体历史→指定写入→回答”，SRU测到另一组端点的读取作用，两者不能直接拼接。本卡真正使用DWB的同一对L11o/L11d端点：在F中只把t2直接读取的状态来源换回O，净供体转移分别由0.635降至0.097、由0.465降至0.028；冲突配对的自身回答由39/168升至120/168、由79/168升至159/168。全部臂348/348交付有效完整编号，无停止或截断。这将来源选择的撤回明确接到后续直接读取，排除了“只是读坏后失分”的解释。

获得侧也有实测内容：O只在t2直接读取中使用F的状态，G为0.396与0.271，区间均为正。两方向的D−E配对差在G与W上均为正；E单独不产生同样的获得作用，N4146的E撤回反而增加净供体转移。联合DE没有使获得侧通过M判据。本文因此可以写**历史来源经指定写入形成的差异，在后续直接读取上具有可操作的选择作用**，并同时报告获得量级未确认。

**没有补齐的部分。** 全部D/DE获得侧的区间下界均小于.25；预登记的强双向连接结论未获完整支持，G0只能记为部分补齐。不能把正区间、p值或D/E差异替代原门槛。也没有检验自然唯一通路、位置/实体/编号编码、跨任务跨模型机制或完整原生停答原因。

**论文如何累积。** 保留DWB已经成立的写入构造及反向自身恢复；增加同一写入端点上读取用途的因果约束、撤回及正向获得证据。主问题没有缩小，也不是只新增一个小条件。下一优先是新材料上的来源—写入—读取预测与获得量级检验，先依据场景异质性和目标精度定容量，不直接把旧48输入或预留24情境当成足够。新材料需解耦位置、实体和编号；不自动扩层、时刻或模型找阳性。本轮未新增下一实验设计或执行。

##### 4. 工程验收、失败与预算

执行代码：Git `19d403597`；本轮有效冻结 `faa4c2a7e9f5ca4450ae6c72b52c5dfc1ffc6d3eb014eb8a32697d36c5687aa9`（127文件）。CPU验收7项通过，资产和旧依赖检查通过。

首次预检r01错误地要求本卡两方向的形成摘要字典与旧LVK四方向字典整体相等，22.618秒后停止；没有读取实验结果。按预登记允许的一次工程修复，改为当前字段集合完整且每项摘要精确对应，增加缺失/篡改回归测试，重新CPU验收和冻结。未放宽数值容差、科学门槛或预算。失败原件、旧freeze及Git源版本保留，详见[D1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/deviations/D1-preflight-schema.zh-CN.md)。

预检r02：每场景首ID接收者及全部同场景供体，两方向全臂618条；通过旧输出重放、96次零用途t2逐位检查、FP64及DE局部参照、来源缓存和钩子检查，466.602秒。实测保守外推正式3744.484 GPU进程秒，小于7200秒上限。两张卡均空闲且显存充足，正式按场景分到GPU0/1各一worker，没有终止其他任务。

| 阶段 | GPU进程秒 | 状态 |
|---|---:|---|
| preflight-r01/worker-0 | 22.618 | failed |
| preflight-r02/worker-0 | 466.602 | completed |
| formal-r02/worker-0 | 957.668 | completed |
| formal-r02/worker-1 | 641.720 | completed |

合计 **2088.608 GPU进程秒 = 0.580169 GPU进程小时**，包括模型加载、资产核验、缓存形成、失败、预检、正式和保存；总上限9000秒，正式单独上限7200秒。两卡重叠时间仍分别相加。CPU测试/离线分析不冒充GPU实验。

正式5112条完整轨迹=4176新读取反事实+792端点重放+144身份参照；936次t1来源前向、144份形成、792次零用途单步检查。原函数`trajectories`不计首步停止，计数差异不表示缺记录；全量以各接收者`n_runs`和臂集合验收为准。

##### 5. 原始材料与复核

- [运行合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/CONTRACT.zh-CN.md)、[实现自查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/DESIGN.zh-CN.md)、[设计与判据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-donor-write-readout-plan-v1-2026-11-07.zh-CN.md)。
- [正式验收](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/runs/formal-r02/verification.json)、[预检验收](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/runs/preflight-r02/verification.json)、[CPU验收](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/readiness/cpu-receipt-r02.json)。
- [冻结判读](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/analysis/dwr-readouts-formal-r02.json)、[分析源码](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/dwr_analysis.py)、[统计与分类源码](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/dwr_core.py)。
- 完整原始回答：`runs/formal-r02/worker-0/records/`与`worker-1/records/`，receipt中逐文件SHA；预检与首次失败原件同样归档。
- [交付复核](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/analysis/delivery-audit.json)：全量计数、旧端点输出、来源哈希、预算核对；属于作者自查，不是独立评审。

没有把新材料、9B或另一种时刻/层集合加入本次运行；下一研究选择依据实际结局回到论文证据缺口。

---

### 原件 6：DWR-01 实现前自查

原路径：`experiments/cache-donor-write-readout-v1-2026-11-07/DESIGN.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/DESIGN.zh-CN.md) · [单独阅读副本](../library/9aa7bae19f07b505.md)；SHA-256：`9aa7bae19f07b5051ea4d6a265aa00341011bfd40b0bab9e3cc89a7dd8314627`。

---

#### DWR-01 实现前自查

本卡科学设计沿用已交付[完整C01–C14、E01–E26及对抗审查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-donor-write-readout-self-check-v1-2026-11-07.zh-CN.md)。本次是作者自查，不是独立评审；CPU与模型数值验收另留回执。

##### 与前版比较及C01–C14

| 项 | 本次决定与理由 |
|---|---|
| C01 | 总问题仍为稀疏干预如何通过写入、状态使用影响完整答案；不缩成首token问题。 |
| C02 | 连接DWB纯局部写入与SRU用途；旧端点不同，故有实质新测量。 |
| C03 | 两方向、全348配对不变；已见材料只做开发。 |
| C04 | O/F、t1/t2及各层当前驱动定义不变，供体是状态来源不是整条轨迹。 |
| C05 | 原端点、C0/L00、零用途和D/E/DE获得/撤回齐全；不添无关臂。 |
| C06 | 数值恒等只作工程检查，科学读数来自之后完整自然回答。 |
| C07 | 固定输出D_tr为零；撤回须另有自身恢复，不能靠失分过关。 |
| C08 | 数据按场景重抽；R保留168配对权重，避免接收者配对数不同导致估计对象漂移。 |
| C09 | M、交付护栏、所有结局冻结；不以结果调阈值。 |
| C10 | 二方向分别判读、全用途交付，保留负向/联合/不可判。 |
| C11 | 仅复用已冻结写入和读取算子；新组合仍须预检。 |
| C12 | 每场景固定首接收者全臂预检；源缓存与模块恢复检查覆盖正式全量。 |
| C13 | 最多2 worker，按GPU进程时间预算，模型载入/失败/保存都计入。 |
| C14 | 本次明确授权允许验收后上卡；与自查、数值通过和科学结果分开登记。 |

##### 主要历史错误及实现修正

沿用既有E01–E26清单。本次重点防范：只报失分；重复计独立单位；只用第一token；错误把k/q固定扩到全轨迹；把双用途输出替换称整个状态替换；预算漏加载/影子/失败；授权文件重写字节不同；看到结果再改判据。旧冻结文件全部只读；新源码单独目录。

##### 对抗复查

1. “D/E局部公式成立就算桥接”：否。公式仅验收，完整供体方向回答是科学终点。
2. “读补丁泄漏到t3或缓存”：旧RHook只包自然生成的第一步；CPU核对原生S2，正式确认核函数恢复/无钩子及输入源未修改。
3. “只抽AL省计算”：否。D_tr需要对照供体，全部保留。
4. “六场景几千轨迹足以确认”：否。报告开发性区间、场景数，独立材料缺口保留。
5. “不同配对数下R平均随手写”：已明确R按168逐对差与场景重抽，原始变化也交付。
6. “并行时只算最长worker”：否。合计各worker GPU进程秒；双worker保守限各3600秒。
7. “旧方案未上卡授权要求再问”：本次用户已明确授权；先完成具体验收，不重复请求。

目前结论：设计可实现；是否放行由CPU和实测预检决定。本文件不预告结果。

---

### 原件 7：D1：首次预检形成哈希字段范围错误

原路径：`experiments/cache-donor-write-readout-v1-2026-11-07/deviations/D1-preflight-schema.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/deviations/D1-preflight-schema.zh-CN.md) · [单独阅读副本](../library/fd6d4acfb4d7ee67.md)；SHA-256：`fd6d4acfb4d7ee67e7a5db31f648eeaf9312d9a15d650d79e183da1cd006d19a`。

---

#### D1：首次预检形成哈希字段范围错误

首次模型预检r01在第一个场景形成第一个输入后退出，未生成读取实验结果。源版本Git `c16d60925`、freeze `c369315d3bb41f1a74701a1c0ac65600cda018330b6f1623b788b4ff46e32f70`；原始运行及失败日志保留在`runs/preflight-r01/`。

根因是DWR使用两方向，旧LVK形成哈希记录还包含R0/C1343另外两方向；新代码误用整个字典相等，而DWB已有实现是逐当前字段核对。不能由此次异常推断张量实际不同，也不能忽略数值身份校验。

修正：先要求本卡字段恰为base_b、C_b、两个已登记T方向，再要求每一个值等于旧参考。增加CPU回归测试：允许旧参考附加方向，每个当前字段改变或缺失都必须失败。保持每个摘要的精确比较；未放宽容差或删掉当前方向。更新PLAN_ID为r02，重新CPU验收和冻结；唯一工程重试为preflight-r02。科学端点、臂、统计、生成与时间预算均不变。

本偏离为工程错误，不是阴性科学结果。第一次模型载入和失败时间计入总预算；若重试仍未验收通过，本卡停止，不自动第三次上卡。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [analysis/delivery-audit.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/analysis/delivery-audit.json) | {"status": "passed"} | {} |
| [analysis/manuscript-sync-audit.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/analysis/manuscript-sync-audit.json) | {"status": "passed"} | {} |
| [readiness/cpu-receipt-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/readiness/cpu-receipt-r01.json) | {"status": "passed"} | {} |
| [readiness/cpu-receipt-r02.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/readiness/cpu-receipt-r02.json) | {"status": "passed"} | {} |
| [runs/formal-r02/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/runs/formal-r02/controller.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-07T04:05:37.432002+00:00", "finished_at": "2026-11-07T04:21:40.659447+00:00"} |
| [runs/formal-r02/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/runs/formal-r02/verification.json) | {"status": "passed", "stage": "formal"} | {"verified_at": "2026-11-07T04:21:40.659261+00:00"} |
| [runs/formal-r02/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/runs/formal-r02/worker-0/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-07T04:05:41.002202+00:00", "last_record_at": "2026-11-07T04:21:36.353662+00:00", "finished_at": "2026-11-07T04:21:38.670518+00:00"} |
| [runs/formal-r02/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/runs/formal-r02/worker-1/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-07T04:05:40.938003+00:00", "last_record_at": "2026-11-07T04:16:19.855897+00:00", "finished_at": "2026-11-07T04:16:22.658228+00:00"} |
| [runs/preflight-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/runs/preflight-r01/controller.json) | {"status": "failed", "stage": "preflight"} | {"started_at": "2026-11-07T03:52:34.013825+00:00", "finished_at": "2026-11-07T03:53:01.019817+00:00"} |
| [runs/preflight-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/runs/preflight-r01/worker-0/receipt.json) | {"status": "failed", "stage": "preflight"} | {"started_at": "2026-11-07T03:52:37.572314+00:00", "finished_at": "2026-11-07T03:53:00.190279+00:00"} |
| [runs/preflight-r02/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/runs/preflight-r02/controller.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-07T03:56:16.789165+00:00", "finished_at": "2026-11-07T04:04:07.883153+00:00"} |
| [runs/preflight-r02/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/runs/preflight-r02/verification.json) | {"status": "passed", "stage": "preflight"} | {"verified_at": "2026-11-07T04:04:07.882992+00:00"} |
| [runs/preflight-r02/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07/runs/preflight-r02/worker-0/receipt.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-07T03:56:20.359195+00:00", "last_record_at": "2026-11-07T04:04:04.077096+00:00", "finished_at": "2026-11-07T04:04:06.961653+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有138个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/167-cache-donor-write-readout-v1-2026-11-07.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-readout-v1-2026-11-07)。未复制模型权重、环境或凭据。
