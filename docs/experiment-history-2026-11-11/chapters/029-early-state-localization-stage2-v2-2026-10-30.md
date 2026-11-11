# 029．阶段二：全层缓存差分、层组清理与反向污染

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-10-30T02:03:54.231097+08:00；不能当作全部子运行起止。

**当时的目的与设计**

继续比较早、中、晚干预和缓存组移植，并同时查看候选评分与完整回答，包含审核、预检与正式部分。

**实际过程、结果与后来更正**

累计29112次生成、58224条候选评分；L0新题TTT完整交付0/24，组4干净替换为7/24，中晚TTT仍有96%–100%交付。全线性组与单组4的分差作用不同。本章保留原操作定义与后来的严格阅读更正，次数不是独立问题数。

**来源身份**：`early-state-localization-stage2-v2-2026-10-30`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：全层缓存差分与阶段二深度比较合同草案

原路径：`experiments/early-state-localization-stage2-v2-2026-10-30/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/CONTRACT.zh-CN.md) · [单独阅读副本](../library/6681a1190f5800db.md)；SHA-256：`6681a1190f5800dbfb5874969f886c04a4402d9d620f3e8de445d2e14e470dac`。

---

#### 全层缓存差分与阶段二深度比较合同草案

版本：draft-r02；日期：2026-10-30。状态：未冻结、未授权运行。直接替代本目录draft-r01草案，旧版由Git提交7b0e24d保存；历史已冻结实验不修改。

##### 1 授权和阶段顺序

用户纠正为“把之前那个阶段二的版本给改了，改成先做全层差分，然后再做阶段二的深度比较”。此前“暂时不跑”继续有效。当前只编辑方案与合同，不运行实验、模型预检、队列或巡检。

执行顺序：G全层缓存类型差分 → II-A开发层组扫描 → II-B新题双向验证。所有执行须以后明确授权，并完成第12节冻结。研究输出是指定条件的效应，不是给缓存或通道命名功能。

##### 2 固定模型与条件

模型为阶段一Qwen3.5-4B确切revision、权重、BF16、聊天模板、原EOS集合、greedy、128新token上限。插针仍在MLP中间激活进入down_proj之前；剂量±1及校准提示、公式沿用early-input-control/early-state-localization的冻结引擎。实施前必须抄录精确值、依赖版本和SHA，不以名称推断。

G主条件64个：L0–L31，每层一个固定通道×正负两个符号。通道直接读取experiments/layer-dose-survey-toy-v1-2026-10-27/selection.json中4B的既有32点，不重新抽样、不按旧输出挑点。这里只复用点位；旧八题的校准数值不挪用于当前24输入，剂量校准使用上述缓存实验的冻结规则。实施前导出64条件ID和32点映射及哈希。

此为固定通道面板，不是各层神经元的随机总体估计；原强效锚点不强行替代入选点。历史锚点结果只作参照。共同方向、额外通道和弱剂量均不在本版执行网格内。

##### 3 输入与数据身份

G使用旧development 24输入和旧confirmation 24输入，各为12基础情景的两个事实版本。两面板均已在历史工作中接触，后者称历史复核，不包装成新的盲确认。II-A只用旧development。

II-B另准备12基础情景、24输入，三任务族各四情景；两事实共用候选对，正确项互换。完整题面、答案、候选、ID、审核记录及哈希必须在任何G干预输出打开前锁定。不能只换旧题实体名。

新题须逐题检查唯一可判定核心，披露模型辅助审核身份。获准实施后，干净生成须24/24核心正确且无核心矛盾，各情景clean S>0；失败保留原版本，最多一次修订且须在G输出打开前完成，再失败停止。预标记clean S<2 nats的小分母题，不根据干预效果删题。新题干净审核属于未来推理授权范围，当前不执行。

##### 4 G全层缓存差分操作

同一输入前n−1位无针建立C、有针建立T；读最后提示token及全部生成均不插针。三位码顺序固定为KV、递推R、conv V，C/T表示该类取自哪个完整来源。

| 臂 | 组合 | 含义 |
|---|---|---|
| G0 | TTT | 全污染 |
| G1 | CCC | 全干净 |
| G2 | CTT | 只清理KV |
| G3 | TCT | 只清理递推 |
| G4 | TTC | 只清理conv |
| G5 | TCC | 只清理两类线性状态 |
| G6 | CTC | 仅递推污染 |
| G7 | CCT | 仅conv污染 |

全部类型跨所有对应模型层替换；KV的K、V同时替换。每条生成和每条候选评分各用混合缓存的独立深拷贝。CCC按输入共享，其余七臂按条件保存。张量完全相等的条件仍保留设计身份与来源审计，不能按无效删掉。

##### 5 层间比较与结构控制

展示L0–L31完整曲线。预定窗口早L0–3、中L12–15、后L24–27，每窗口层数相等；L4–11、L16–23以及末端L28–31全部保留，不能从主窗口结论外推它们。

每个插针层报告可受影响的下游KV/递推/conv层数、实际T/C不同的层及张量差范数、全污染的绝对损伤及各臂效应。只有下游层的缓存有结构性写入机会；同层注意力先于MLP。L31在本协议下预期缓存与干净相同，是结构边界对照。若预检发现不符，先检查hook时序和状态，不将其当机制发现。

各窗口内先按符号和层等权平均，再对12情景报告配对差。正负效应另列，避免抵消掩盖。主要用绝对D/S变化，不用接近零的总损伤作分母。可受影响层数与插针深度耦合，本设计不能完全分离二者；不靠一个回归调整就宣称纯深度因果。

##### 6 从G到阶段二的选择规则

只使用G的development全污染与干净读数。每个预定窗口分别选择：停止优势增加最大的条件一个；事实敏感度损失最大的条件一个。条件内先按12情景等权平均，停止每情景两事实等权平均。精确同分依次取层号小、通道号小、负号在前。

最多六唯一条件，重复条件合并但保留入选角色。效应弱、负向或无EOS也不补选；明确标记未显示相应异常。历史复核不参与筛选。阶段二是目的性选例，不能用这些极值代表该窗口平均情况。

锁定选择清单与G完整结果后才进入II-A。G未完成或工程验收失败不得继续。无科学效果不触发改通道、加剂量或改题。

##### 7 II-A缓存深度扫描

| 组 | 递推和conv层 | KV层 |
|---|---|---|
| G0 | 0、1、2 | 3 |
| G1 | 4、5、6 | 7 |
| G2 | 8、9、10 | 11 |
| G3 | 12、13、14 | 15 |
| G4 | 16、17、18 | 19 |
| G5 | 20、21、22 | 23 |
| G6 | 24、25、26 | 27 |
| G7 | 28、29、30 | 31 |

每个入选条件、每组做七个非空清理子集：KV、R、V、KV+R、KV+V、R+V、KV+R+V。背景全T，仅指定组/组件换C。其余状态不动；上游T=C组原样保留。模型配置不匹配层表即停止。

每个入选角色选一个候选组：按该组KV+R+V联合清理对该角色主读数的改善排序，同分取组号小。若同一条件同时入选停止和事实角色，两角色可各选一组；角色总数最多六，故候选“条件×组”最多六。联合臂排名可能遗漏单项有效而联合弱的组；完整单项结果保留，不能事后追加为确认结果。弱或负改善也按规则选并标记，防止隐藏失败。

##### 8 II-B新题双向验证

在新24输入上，对最多六个候选条件×组，保留七组件子集，两方向共14臂：污染背景中清理指定组；干净背景中只污染指定组。生成与评分独立深拷贝，缓存位置及管理状态匹配。重复的条件×组×子集×方向只算一次。

另对每个唯一条件采集G的八种全局组合，新面板CCC共享。全局参照用于检查所选异常是否在新题上存在；即使未复现也保留全部结果，不能换题或换候选。候选组、角色、代码、分析须在任何II-B干预结果打开前锁定。

本版终点为组级验证，不自动细分单层、头、K/V或conv时间槽。

##### 9 读数、统计与解释

所有阶段所有条件同时采集停止和事实读数，不根据先看到的症状选择性测量。

D=max EOS logit−max非EOS logit。停止清理效应D(T)−D(清理)，反向效应D(污染)−D(C)。并列首步EOS、逐步D、首次停止位置、生成长度、结束原因、交付、重复和矛盾；128上限是截断，不是自然停止。

事实S(b)=[ll(A)−ll(B)]事实A−[ll(A)−ll(B)]事实B；清理效应S(清理)−S(T)，反向效应S(C)−S(污染)。R仍为median_b[S(臂,b)/S(C,b)]，0.897旧参照下界仅描述历史可比性，不当新数据等效性界值。S为主，R并列。预标记小分母题另作排除后的敏感性分析，报告剩余数量，不替代完整主分析。

G和II-A为探索性完整效应图：逐题差值、均值、中位数、方向一致数及情景级bootstrap95%描述区间（10,000次，分析种子20261030），不挑显著层作总体结论。已有两面板用于观察稳定性，不声称独立复现。

II-B确认性主比较仅为每个角色候选组的“三类联合替换”清理及反向两个方向，最多12个检验；12基础情景全部4096符号翻转，单侧，实际完整主比较家族Holm校正α=0.05。同一条件×组但不同角色测不同读数，仍分别计比较。其余六子集和跨角色读数全部报告为探索性，不能借未校正p值追加确认结论。符号翻转要求零假设下情景差值可交换；固定题集不代表任务总体。基本单位始终为基础情景，不是token、条件或生成条数。

描述区间不是同时置信区间；多条件与两事实相关性保留在情景内。连续尺度的二阶交互按同一背景计算E(X+Y)−E(X)−E(Y)，三阶用完整八组合的包含排除计算；不将中位R相加解释成贡献份额。交互发现仍为探索性。

检出改善不等于完整恢复，未显著不等于零效应。清理和反向均有效仅支持指定背景中的双向效应；不能推出唯一根因、天然功能分区或信息彻底丢失。

全部自由回答隐藏层号、条件、缓存臂和方向后阅读，先锁标签后揭盲；记录核心跟随、另一事实答案、其他错答、未交付、无法判定，以及核心矛盾、附错、重复和截断。固定种子20261031抽10%唯一回答第二阅读，保留分歧；披露模型辅助，不伪称人类审核。题面与文本完全相同可去重阅读，但映射回全部来源，不把复制计为独立证据。

##### 10 其他状态及生成途中扩展

本轮三类内容缓存是KV、递推、conv。实施前审计实际冻结版本中的所有可变字段：初始化/历史存在标记、位置与长度、模型级位置状态等。管理状态须符合相同前缀和调用路径，不随意当语义供体交换。若发现三类以外随干预变化、且可影响下一步的持久状态，暂停并修订合同，不能假定已覆盖全部状态。

Q、残差、门控、logits属于当前计算；已生成文字属于外部历史输入。冻结实现之外的最新库行为不能替代核验。

提示缓存差分无效不能排除持续注入或生成期作用。若G显示中后层提示污染弱，而历史full注入已有异常，记录为生成途中拆分的候选问题；不同协议历史结果只提供线索。该扩展本版不执行，须另行设计同一固定文字前缀、等位置的C/T重建及有针/撤针对照，不能直接拼来自不同回答的缓存。不设自动追加队列。

##### 11 规模、复用和停止

G每面板(64条件×7非共享臂+1共享CCC)×24=10,776生成；两面板21,552。

II-A最多6唯一条件×8组×7子集×24=8,064生成；全局参照复用本轮G development同身份记录，不另计。实际复用必须核对记录/环境/代码路径/校准/分数哈希；不一致则停止查因，不静默重跑或增加预算。

II-B最多6条件×组候选×7子集×2方向×24=2,016局部生成；最多六唯一条件的全局参照(6×7+1)×24=1,032；合计最多3,048。

正式合计上限32,664生成，附65,328条候选序列评分，去重或少于六候选则减少。新增干净题审核每版24生成+48候选，最多两版；每个G/II-A/II-B阶段工程预检最多128生成+256候选，共最多384生成+768候选。其他前向审计需逐项有界清单；预检、失败、审核与正式成本分列。当前全部零执行。

预检后才估墙钟、GPU占用与磁盘，须有资源上限及授权才能正式运行，不凭早层短回答吞吐承诺时间。预算不接受则冻结前缩范围，不能运行后删分母。

必须验证三类缓存读写有效、深拷贝无串扰、C/C与T/T同路径精确恒等、候选评分索引、hook恢复及权重一致；新增八组合、八组、L31结构边界、双向来源和去重测试。每记录保存完整来源审计、token、分数与版本身份。

来源不符、非有限数、记录缺失、冻结变化、预检失败则停止阶段并保留partial；修复另版预检，不覆盖失败。效应弱不是技术失败，也不许可重抽通道。冻结源目录只读，派生分析写独立目录；不临时移文件掩盖冻结变化。不抢占其他任务、不自动下载模型或清理服务器。

##### 12 冻结前清单与交付

尚须补齐：用户对具体范围与运行的授权；64条件精确清单与来源SHA；模型、引擎、校准身份；新24输入与审核；实现及分析代码；CPU合成验证和各阶段GPU预检清单；执行网格及记录ID；资源预算与退出策略。未补齐前本文件只是可审阅草案。

交付G完整32层缓存类型差分、窗口与结构边界解释、II-A完整组图、候选选择收据、II-B新题双向结果、全部原文与阅读、失败与成本。全层筛查结论限固定点位；新题仅验证选择的局部候选，不替代全层新题复现。

本次仅原位修订方案与合同，不新增实验目录，不执行新模型推理，不自动启动后续单层、K/V或生成途中实验。来源链接见PLAN.zh-CN.md。

---

### 原件 2：全层缓存差分与阶段二深度比较方案

原路径：`experiments/early-state-localization-stage2-v2-2026-10-30/PLAN.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/PLAN.zh-CN.md) · [单独阅读副本](../library/673a08d65385f8a4.md)；SHA-256：`673a08d65385f8a49c6fe07e751a785e092b754ccfcad8a5c8300a19bec06e4e`。

---

#### 全层缓存差分与阶段二深度比较方案

日期：2026-10-30。版本：draft-r02。状态：待审阅、未冻结、未授权运行。

本次直接修订原阶段二文档，文件位置不变。draft-r01 已在 Git 提交 7b0e24d2e26f3f5cab31cf5296048b710f75546d 保存。新顺序为：**先做全层插针的缓存类型差分，再做阶段二的缓存深度比较。** 配套规则见 [合同草案](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/CONTRACT.zh-CN.md)。

##### 两个不同的深度维度

第一步的横轴是插针层：在 L0–L31 分别插针，比较更换 KV、递推、conv 后的变化。第二步的横轴是被替换缓存所在层：对前一步选出的条件，寻找异常依赖哪一段缓存。

停止与事实利用始终分别记录，所有条件同时采集两种读数。不能把开始输出当作事实利用恢复，也不能用低事实敏感度断言内部信息彻底消失。

##### 第一步 全层缓存类型差分

建议主网格为 Qwen3.5-4B 全32层、每层一个既有固定通道、±1两种剂量，共64条件。点位沿用旧逐层剂量调查的4B清单，不按效应重新选点。全层覆盖不等于全通道覆盖；这一成本选择限制了结果对每层通道总体的代表性。

对提示前 n−1 位建立干净 C 和污染 T 缓存，再逐类拼接，末位及生成不插针。测试 KV、递推、conv 的全部八种 C/T 组合，包含之前遗漏的“仅递推污染”和“仅conv污染”。开发与历史复核面板各24输入，展示完整逐层曲线，并比较预定的早L0–3、中L12–15、后L24–27窗口；其余层不删，L28–31末端结构另列。

这一步回答：随插针层变化，停止竞争、事实敏感度及不同缓存替换的效应是否不同？结果可能是明显差异，也可能主要由可被影响的下游层数量解释；两种结果均保留。

##### 阶段二 缓存深度比较

第一步后，在三个预定窗口内，分别按停止损伤和事实敏感度损伤选择一个条件，最多六个唯一条件。只用开发面板排名，历史复核面板不参与挑选。弱效应也不换题、补点；标记本窗口没有明显损伤。

阶段二A在旧开发题上扫描八个缓存深度组。每组比较三类缓存的七个非空清理子集，包括各单项、各两两组合和三者联合。这样不预设早层的缓存结论也适用于中后层。

阶段二B只对每个选定条件排名最高的一组做新题双向验证：既在污染背景中换干净，也在干净背景中加入该组污染。每组仍保留七种组件子集，不按单项结果挑组件。新题在任何第一步干预结果打开前锁定。

##### 结构差异与解释边界

- 插针发生在MLP，而同层注意力先执行。晚层插针可影响的下游缓存更少，必须逐层审计T/C差分，不把这一差异直接解释成缓存功能分工。
- 最后一层MLP在本提示前缀协议下没有下游缓存写入机会。L31作为结构边界对照保留；无效不代表它对当前token输出不重要。
- 某类缓存全部换干净只恢复部分读数，不等于该类存储固定比例的事实。
- 局部清理有效只定位到可改变异常的位置；反向污染也有效，才加强该位置在指定背景下的双向因果证据，仍不证明唯一根因。
- 提示末尾的缓存操作不能覆盖持续注入、生成中途或文字历史维持的所有异常。生成途中拆分列为后续独立扩展，不自动接入本轮，避免混用不同文字前缀的缓存。

##### 缓存及其他状态

本轮内容状态为K、V（合称KV）、递推状态、conv状态。运行前核查缓存管理字段和模型其他可变字段；它们须匹配，但不作为第四类语义缓存任意交换。Q、残差流、门控与logits属于当前计算，已生成文字属于历史输入。K/V、头、conv时间槽等更细拆分暂不列入本轮。

##### 规模与交付

| 阶段 | 自由生成次数 |
|---|---:|
| 全层差分：开发与历史复核 | 21,552 |
| 阶段二A：最多六条件，八组扫描 | 最多8,064 |
| 阶段二B：新题双向验证及全局参照 | 最多3,048 |
| 合计 | 最多32,664 |

每次生成另附两条候选评分；去重、旧参照复用与额外预检预算见合同。这比原草案9,120次更大，增加量主要来自全层八组合覆盖。小时数须未来获准后用预检测量，不能沿用早层短回答吞吐估算。

交付分为全层差分图、阶段二层组图和新题验证三部分；所有原文、失败、无效条件、选择规则与收据均保留。旧confirmation仅称历史复核，不称新独立确认；新题只确认选中候选，不确认所有32层的总体规律。

##### 来源与修订边界

- [阶段一缓存拆分合同](https://github.com/yuxiexiong/acupuncture/blob/34e5d4a4533d3cbbe3a0994b7d80d060bb336a9f/experiments/early-state-localization-v1-2026-10-29/CONTRACT.zh-CN.md)
- [阶段一结果](https://github.com/yuxiexiong/acupuncture/blob/34e5d4a4533d3cbbe3a0994b7d80d060bb336a9f/experiments/early-state-localization-v1-2026-10-29/REPORT.zh-CN.md)
- [既有4B点位来源](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/selection.json)

本次只改原方案与合同；不另建一套计划，不改历史实验，不运行模型，不将文档审阅视为实验授权。

---

### 原件 3：全层缓存差分与阶段二深度比较：结果报告

原路径：`experiments/early-state-localization-stage2-v2-2026-10-30/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/REPORT.zh-CN.md) · [单独阅读副本](../library/6ae2cf4b772e4ee6.md)；SHA-256：`6ae2cf4b772e4ee68dfe487da9edaf64af55254a29a593ab84f704efd0440f58`。

---

#### 全层缓存差分与阶段二深度比较：结果报告

日期：2026-10-30（UTC 2026-10-29 18:03–23:17 跑完）。合同 draft-r02，冻结 `freeze-r01.json`（sha256 `bb81a890…`），用户授权全流程、每卡 4 worker、表中事项预先放行（原话见 `readiness/authorization-*.json`）。Qwen3.5-4B，冻结引擎与环境同阶段一。

##### 先说不利的部分

1. **中、晚层条件的异常基本不到回答层面。** 全污染（TTT）下，中层窗口（L12–15）开发/历史复核分别有 94%/86% 回答跟随事实，晚层（L24–27）100%/98%；II-B 新题上中、晚层四个角色 TTT 跟随率 96–100%。这些条件的停止优势 D 上升与事实敏感度 S 下降都显著，但属**阈下读数**：II-B 对它们的“检出”是内部读数的组级定位，不是可见失效的定位。
2. **能打坏回答的只有 L0 条件，而它的停止异常没有被任何单组定位。** L0/C4146 −1 的 D 上升 20.3（新题），最佳单组（组 4，L16–19）三类联合清理只去掉 3.2（16%）；全局清理线性层状态（递推+conv）去掉 16.4。新题上 TTT 0/24 跟随事实（24/24 未交付），只清理组 4 恢复到 7/24（29%）。
3. **early:fact 的清理方向未检出**（Holm p=0.073，均值 0.68，95% 区间 [−0.14, 1.48]），开发面板选择时已标“未超出选择零分布”。同组单独污染却能复现约一半 S 损失（7.6/14.7）——清理不足、污染足够，提示多深度冗余承载（推测档，未检验）。
4. **晚层（L25）组 7 的高份额是结构必然的弱证据**：L25 插针后可受影响的下游只有 L26–31，组 7（L28–31）几乎就是全部下游。
5. 所有回答阅读均为**模型辅助**（Claude 子代理盲读 + 10% 独立第二阅读），没有人工读者；II-B 新题也由同一模型起草与审核，独立性弱（已披露）。首轮读者对“先错后改”“截断”类回答的口径不一，锁定前做了盲态统一（见 §5），统一规则在重读前写死。

##### 1 执行概况

| 阶段 | 生成 | 候选评分 | 墙钟 h | 结果 |
|---|---:|---:|---:|---|
| 新题干净审核 audit | 24 | 48 | 0.01 | 24/24 核心正确、无矛盾；12/12 情景 clean S>0（5.35–24.87），无 S<2 |
| G 预检 | 44 | 88 | 0.04 | 全部门槛通过（含阶段一全部门槛、八码与阶段一逐字节一致、112 项来源审计、L31 全张量 T=C、插针层及以前缓存 T=C） |
| G 开发 | 10,776 | 21,552 | 1.51 | 核验通过 |
| G 历史复核 | 10,776 | 21,552 | 2.28 | 核验通过 |
| II-A 预检 | 32 | 64 | 0.02 | 通过；复用的 G 开发 TTT/CCC 记录逐字节重放一致 |
| II-A 扫描 | 5,376 | 10,752 | 0.97 | 核验通过（4 唯一条件，低于上限 8,064） |
| II-B 预检 | 44 | 88 | 0.04 | 通过 |
| II-B 验证 | 2,040 | 4,080 | 0.32 | 核验通过（4 唯一条件×组，低于上限 3,048） |
| **合计** | **29,112** | **58,224** | **5.19**（双卡约 10.4 GPU h） | 0 次失败、0 次重试 |

##### 2 G：全层缓存类型差分（探索性，两面板）

- 两面板逐条件损伤高度一致：停止 r=0.993，事实 r=0.97。
- 损伤随插针深度下降（与可受影响下游层数同向，本设计无法分离二者，合同 §5）；**L31 两读数恰为 0**，结构边界成立。
- **首步 EOS 只出现在 L0（±1 均 24/24）**；L1 起 D 仍升 12–18 但首步不停。
- **停止异常各深度都主要由线性层状态承载**：开发面板上全局只洗递推+conv（TCC）去掉 D 损伤的约 45–90%（L0–L29，逐条件 0.42–0.89）；新题上 L0/C4146 −1 只洗 KV 仅去掉 0.84/20.3。
- **事实异常的承载随深度转移（描述性）**：早、中层（L3–L15）只洗线性层去掉 0.5–0.9；L17–L22 只洗 KV 去掉 0.7–0.9（该处损伤仅 1–3，比值噪声大）。
- 回答层面：早层窗口 TTT 跟随率开发 27% / 历史复核 14%（大部分未交付），只洗 KV 升到 71%/62%，只洗线性层 82%/48%。

完整逐层曲线、窗口汇总、交互项与结构差分见 `analysis/g_development-r01.json`、`analysis/g_history-r01.json`。

##### 3 选择（冻结规则，仅开发面板）

| 角色 | 条件 | 损伤（开发） | 标记 | II-A 选组 | 组联合清理改善（开发） | 标记 |
|---|---|---|---|---|---|---|
| early:stop | L0/C4146 −1 | D +21.1 | — | 组 4 | 3.2 | — |
| early:fact | 同上 | S −14.3 | — | 组 4 | 1.7 | 未超出选择零分布 |
| mid:stop | L14/C8351 +1 | D +11.2 | 无首步 EOS | 组 7 | 5.7 | — |
| mid:fact | L12/C3621 −1 | S −8.0 | — | 组 4 | 5.3 | — |
| late:stop | L25/C2747 +1 | D +4.5 | 无首步 EOS | 组 7 | 4.1 | — |
| late:fact | 同上 | S −2.2 | — | 组 7 | 2.2 | — |

位于插针层及以前的组改善恰为 0（结构边界在实测中成立）。锁定收据：`readiness/g-lock-r01.json`、`readiness/a-lock-r01.json`。

##### 4 II-B：新题双向验证（确认性，12 检验，Holm α=0.05）

单位为 12 个基础情景，4096 符号翻转精确单侧检验。

| 比较 | 均值 [95% 描述区间] | 正向情景 | Holm p | 判读 |
|---|---|---|---:|---|
| early:stop 组4 清理 | D −3.21 [2.80, 3.66] | 12/12 | 0.003 | 本面板检出 |
| early:stop 组4 污染 | D +5.61 [4.90, 6.28] | 12/12 | 0.003 | 检出 |
| early:fact 组4 清理 | S +0.68 [−0.14, 1.48] | 10/12 | 0.073 | **证据不足** |
| early:fact 组4 污染 | S −7.64 [4.64, 10.47] | 11/12 | 0.003 | 检出 |
| mid:stop 组7 清理 / 污染 | 5.31 / 5.01 | 12/12 | 0.003 | 检出 |
| mid:fact 组4 清理 / 污染 | 6.47 / 6.68 | 12/12 | 0.003 | 检出 |
| late:stop 组7 清理 / 污染 | 4.65 / 4.68 | 12/12 | 0.003 | 检出 |
| late:fact 组7 清理 / 污染 | 1.97 / 2.17 | 12/12 | 0.003 | 检出 |

11/12 检出。“检出”只表示指定背景、本固定面板中的平均方向效应，不等于完整恢复或唯一根因（合同 §9）。

**份额（探索性，组联合清理 / 新题全局损伤）：** mid:fact 72%（6.47/8.96），且主要来自**组 4 的递推状态单项**（清理 5.27、污染 5.75）——本轮最干净的深度定位；mid:stop 51%，分散在三类；late 94–96%（结构必然，见上）；early:stop 16%；early:fact 清理 5%、污染 52%。

##### 5 回答阅读

| 面板 | 唯一回答 | 首读 | 统一与裁决 | 10% 第二阅读一致率 / κ |
|---|---:|---|---|---|
| G 历史复核 | 5,216 | 12 名盲读子代理 | 读者口径不一，锁定前两轮盲态统一（452+68 条），10 条分歧逐条裁决 | 512/522（98.1%）/ 0.943 |
| 开发（G 开发 + II-A） | 4,477 | 12 名，统一规则前置 | 43 条“无法判断”按规则复核；5 条分歧裁决 | 443/448（98.9%）/ 0.965 |
| 新题（II-B） | 939 | 4 名 | 1 条分歧裁决 | 93/94（98.9%）/ 0.97 |

统一规则（重读前写死）：核心答案取最后一个明确结论；最终“无法确定/矛盾/拒答”记其他错答；只有在相互冲突的候选仍未收束时被截断才记无法判断。各面板 `reading/*/adjudication-log.json` 保留首读、统一、第二阅读与裁决全过程；标签先锁后揭盲（`lock.json` → `joined.json.zst`）。逐窗口、逐角色的跟随率见 `analysis/reading-summary-r01.txt`。

##### 6 偏离与决策日志

1. 资源上限取用户授权前一条回复中的示例值（墙钟 30 h、磁盘 40 GiB）；实际 5.19 h、约 1 GB 原始记录。
2. 按合同严格读法，G 两面板都完成后才进入 II-A。
3. 阶段串联由服务器端链式脚本执行；首版等待检查有 `set -e` 漏洞（失败阶段可能被记为完成），在任何阶段经由它运行前已修正，并杀掉一个重复的链实例；未影响任何运行。
4. 阅读口径统一与裁决由编排模型在未打开密钥时完成（见 §5）。
5. 一名阅读子代理把暂存文件写入共享 `/tmp/lab`，自称可能覆盖了其中一个既有的 `s.txt`（非本项目文件，无法确认）。之后所有阅读暂存一律限定在本任务目录。
6. 新题由模型起草、模型审核、模型阅读，未经人工检查（预先放行项，已披露）。

失败类型（合同口径）：无合同执行失败。early:fact 清理方向为“没拿到结果”（效应不显著），不是负面证据。

##### 7 可以与不能说的

- 可以：在本面板、本剂量下，指定条件的停止优势与事实敏感度异常可被所选缓存深度组双向改变；中层事实敏感度异常的大部分可由 L16–19 递推状态的单独替换双向改变。
- 不能：中、晚层“定位到了失效”（回答层面几乎无失效）；早层停止“由组 4 承载”（只占 16%）；任何缓存类型的天然功能分工；外推到其他通道、剂量或模型。

##### 8 文件

代码 `stage2.py`、`analyze_stage2.py`、`test_stage2.py`（冻结）；合同 `CONTRACT.zh-CN.md`；实现与决策 `IMPLEMENTATION.zh-CN.md`；授权、锁定、预检与运维日志 `readiness/`；分析 `analysis/`；回答导出 `exports/*-answers.jsonl.zst`（逐条记录已按收据哈希核验）；阅读 `reading/`；运行收据 `runs/`（四个大运行的完整记录与缓存清单另存为 tar.zst：服务器 `/workspace/stage2-ops/archive/`、本机 `~/acupuncture-archive/early-state-localization-stage2-v2/`，哈希见 `runs/*.verify.json`）。

---

### 原件 4：实现说明与决策日志（对应合同 draft-r02）

原路径：`experiments/early-state-localization-stage2-v2-2026-10-30/IMPLEMENTATION.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/IMPLEMENTATION.zh-CN.md) · [单独阅读副本](../library/ad4f144ce0dc2712.md)；SHA-256：`ad4f144ce0dc27121ac5d0dc6c02251026d6bc6955b2479ea3860435a252253e`。

---

#### 实现说明与决策日志（对应合同 draft-r02）

日期：2026-10-30。状态：代码与 CPU 合成测试完成后，用户授权全流程，已冻结（freeze-r01）并跑完；结果见 [REPORT.zh-CN.md](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/REPORT.zh-CN.md)。下文“未做”一节是冻结前的历史状态。

##### 文件

| 文件 | 作用 |
|---|---|
| `stage2.py` | 条件与网格、缓存按组/按类拼接、来源审计、工程门槛、授权链、worker / 控制器 / 核验 |
| `analyze_stage2.py` | G 全层差分图与窗口选择、II-A 组图与候选组选择、II-B 确认检验、干净审核判定、锁定收据；`selftest` 为合成预演 |
| `test_stage2.py` | 在 8 层随机初始化 Qwen3.5（2 组）上的 CPU 测试，不加载权重 |
| `data/validation-r01.json` | II-B 新题 12 情景 × 2 事实（**模型起草**，见下文 §新题） |
| `readiness/cpu-receipt-r01.json` 等 | CPU 测试与自检日志及源文件哈希 |

代码来源：在本仓库阶段一 `early-state-localization-v1-2026-10-29/localize.py`（提交 34e5d4a）之上扩展，直接 import 其缓存原语（`forward`/`decode`/`score`/`audit`/`compose`/`randomize`/`_build_T`/`_clean_cache`/`preflight_gates`）；注入与校准沿用 `early-input-control-v1-2026-10-29/control_engine.py`；§10 管理状态审计复用其 `state_fingerprint`；S、符号翻转复用 `early-stop-knowledge-readout-v1-2026-10-29/analyze.py`。没有引入外部开源代码（阶段一已核对过 split-prefill 实现，本轮的拼接接口与之相同）。

##### 执行顺序与授权链

`audit`（新题干净审核）→ `g_preflight` → `g_development`、`g_history` → `lock-g`（G 选择锁定）→ `a_preflight` → `a_scan` → `lock-a`（候选组锁定）→ `b_preflight` → `b_validate`。

`authorize()` 逐级检查：冻结哈希；新题锁（`clean_audit: passed` 且题文件哈希一致，所有 G 及以后阶段都要）；本阶段预检核验；II-A/II-B 要求 G 锁及 G development 核验（并核对 10,776 条）；II-B 要求 A 锁且授权中的候选与锁一致。锁文件由 `analyze_stage2.py lock-g / lock-a` 生成，生成时若已存在下一阶段 `runs/a_*` 或 `runs/b_*` 输出则拒绝。

##### 规模（测试中逐项核对）

| 阶段 | 生成 | 说明 |
|---|---:|---|
| audit | 24 | 新题 CCC |
| g_preflight | 44 | 每卡 1 输入 × (3 条件 × 7 + CCC)；条件 L0/C4146 +1、L13/C248 −1、L31/C8750 +1（结构边界） |
| g_development / g_history | 10,776 / 10,776 | 64 × 7 + 共享 CCC，× 24 |
| a_preflight | 32 | 每卡 1 输入 × (TTT、CCC 复用重放 + 第一个入选条件 × 组 0、7 × 7 子集) |
| a_scan | ≤ 8,064 | 唯一条件 × 8 组 × 7 子集 × 24；TTT/CCC 复用 G development |
| b_preflight | 44 | 每卡 1 输入 × (CCC + 1 条件 × 7 码 + 1 候选 × 7 子集 × 2 方向) |
| b_validate | ≤ 3,048 | 去重后的局部臂 + (唯一条件 × 7 + 1) × 24 全局参照 |

每次生成附两条候选评分。三阶段预检合计 120 生成 / 240 候选，在合同 384 / 768 之内；另有逐项列明的额外前向（下节门槛内的 1 步解码）。

##### 工程门槛（预检及正式运行）

- 正式每条记录：逐张量来源审计（与设计不符即停）；组合缓存的管理状态与 C 相同；T、C 在生成/评分后哈希不变。
- 每个条件建 T 时：**插针层及其以前的所有缓存必须 T=C**（同层注意力先于 MLP），否则停；逐张量差范数与可受影响层数写入 `caches/*.json`。
- 每个条件建 T 时：除 KV/递推/conv 外的所有缓存字段（实测为 `has_previous_state`、各初始化标记、`conv_kernel_size`、`number_of_states`、`record_past`，没有其他张量或位置计数）T 与 C 必须相同；不同即停并修订合同（§10）。
- g_preflight：阶段一全部门槛（同路径恒等、可读性、增量路径=引擎路径、掩码 hook 等价、注意力读出无副作用）+ L31 全部张量 T=C。
- 所有预检：八码全局替换与阶段一 `compose` 逐字节及首步 logits 一致；8 组 × 7 子集 × 2 方向来源审计；三类可读性。
- a_preflight：重新生成的 TTT/CCC 与 G development 同 ID 记录的校准哈希、提示 token 哈希、token 序列、首步 logits 哈希和候选分数逐项一致，否则停（§11 复用核对）。

##### 合同未写死、由实现决定的事项（冻结前请确认）

1. **选择标记的零分布**。合同要求“弱、负或无 EOS 也按规则选并标记未显示异常”，未给判据。第一版我用了“未校正 p<0.05 / bootstrap 区间不含 0”，合成预演当场证明它**未校准**：从 8 个纯噪声候选中取最大者，常被标成“有改善”。现改为**最大统计量精确符号翻转**（同一符号模式施于全部候选，保留相关性，4096 种），p≥0.05 标 `not_beyond_selection_null`；另标 `non_positive_mean`、停止角色 `no_first_step_eos`。40 个零世界种子实测误标率：G 12/240、II-A 5/240。标记不影响选择本身。
2. **结构与管理状态检查设为硬停止**（合同只说预检发现不符先查 hook 时序）。理由：两者在确定性前向下应当严格成立，不成立即来源不符。
3. **bootstrap**：每个面板规模一张固定索引矩阵（种子 20261030，10,000 次），所有比较共用同一组重采样；区间为逐比较描述区间。
4. **预检条件与组**：见上表；均为开发面板，不含历史复核题与新题干预。
5. **II-B 确认族**：每个角色的 KV+R+V 联合清理与反向污染两项，最多 12 项，按实际个数 Holm（α=0.05）。合成预演：12 项全部检出的世界、零世界 0 项检出；零世界 40 种子任一检出 2/40。
6. **共卡**：用户 2026-10-30 删除“每卡一个 job”规则；本实验每卡多个 worker（见“吞吐与提速”），每个 worker 启动时要求本卡空闲显存 ≥20 GiB 并记录同卡进程；不抢占其他任务（合同 §11）。
7. **干净审核判定**：自动部分为每情景 clean S>0、预标记 S<2；“24/24 核心正确且无核心矛盾”需要阅读标签文件（`analyze_stage2.py audit RUN LABELS OUT`），无标签时状态为 `awaiting_reading`。
8. **候选组排名**按单一入选条件计算（合同 §7 每角色只有一个条件）；同条件两角色可选不同组，`(条件, 组, 子集, 方向)` 重复只跑一次。

##### 新题（II-B）

`data/validation-r01.json` 由 Claude（claude-opus-5-5）起草，三族各四情景，两事实共用候选、正确项互换；结构与旧 development/confirmation 不同（含否定、条件门禁、多步加减、时间推算、相反状态、方位等），测试核对了与旧 48 条题面无重复。**尚未经人工检查，也未做与条件无关的模型辅助题面审核和干净生成审核**；这是合同 §3 冻结前置项，需要你过目。

##### 测试

- `test_stage2.py`：r01 23 项、r02 24 项、r03 25 项全部通过（gqa-h20 `.venv-bench`，torch 2.6.0+cu124 / transformers 5.20.2，CPU，服务器仓库外的临时副本）。覆盖：真实 32 层布局与合同组表一致、不符即停；8 组×7 子集×2 方向来源审计及错设计被拒；深拷贝无串扰；八码与阶段一 compose 逐字节/logits 一致；同路径恒等；门槛函数在小模型上通过且 hook 清净；末层结构边界、上游差异被拒；管理状态一致且变动可被检出；64 条件；各阶段数量 10,776/8,064/3,048、合并与去重；三个预检预算；选择/候选校验；复用重放能检出任何差异；新题结构。
- `analyze_stage2.py selftest`：符号翻转 4096、Holm、同分规则（层→通道→负号）、交互（加性为 0、纯协同三阶为正）、G 窗口选择命中、零世界全部被标记、II-A 候选组命中、II-B 判据可满足也可不满足、干净审核三种结局、小分母敏感性。

##### 吞吐与提速（2026-10-30）

用户指示删除“每卡一个 job”规则、试所有提速方案、可行的直接实施，但不得影响精度与效果。**采纳判据在试跑前写死**：与现行单进程 batch=1 路径相比，逐步全词表 logits 哈希、生成 token、候选对数似然全部逐字节相同才采纳，任何差异即否决。试跑负载：开发题 3 条 × 阶段一锚点 N_L00_C4146_D+1 × 八码 = 每轮 24 生成（不涉及任何新 G 条件）。证据：`readiness/speed-trial-r01.json`、`readiness/speedtrial.py`。

| 方案 | 每卡生成/秒 | 与基线逐字节比对 | 结论 |
|---|---:|---|---|
| 基线：每卡 1 个 worker | 0.53 | — | — |
| 每卡 3 个 worker | 1.52 | 3/3 进程 24/24 相同 | 可行 |
| 每卡 4 个 worker（另一卡同时 6 个） | 1.80 | 4/4 相同 | **采纳** |
| 每卡 6 个 worker | 1.85 | 6/6 相同 | 可行，增益 <3%，显存翻倍，不选 |
| 同一输入 8 臂批量解码 | 1.30 | 24/24 不同，4 条 token 序列改变，对数似然差至 0.28 nats | 否决 |
| 融合线性注意力 kernel（fla 0.6.0；causal-conv1d 无 nvcc 装不上） | 0.27 | 24/24 不同，对数似然差至 0.39 nats，且更慢 | 否决 |
| 缩小设计 | — | — | 改变实验，按指示不试 |

实施：`launch` 按授权文件 `maximum_workers`（偶数，≤12）起 worker，worker w 用卡 w % 2；正式阶段按（输入, 条件）单元轮转分配，预检按输入分配（门槛需要同一输入的全部条件）；每个 worker 槽一把锁，不再按卡加锁；每个 worker 启动时仍要求本卡空闲显存 ≥20 GiB。测试证明 2/4/8/12 worker 的划分都是完整计划的无重复划分。建议运行授权写 `maximum_workers: 8`（每卡 4 个）。

另：r02 已把每条记录的缓存哈希从约 4 遍降为 1 遍（实测一遍约 46 ms，原来约占 4% 时间；审计结果逐项不变）。

**ETA 更新（推测，以 GPU 预检实测为准）**：阶段一同类实测约 5.2 s/条/卡（含共卡），本次试跑单 worker 1.9 s/条（早层锚点回答短，均 19 token）。按每卡 4 worker 约 3.4 倍：G 两面板约 5–9 h，II-A 约 2–4 h，II-B 约 1–1.5 h，合计约 8–15 h 墙钟（原估 25–50 h）。中后层条件回答更长，实际可能落在区间上沿。

##### 未做

没有冻结、没有授权文件、没有 GPU 预检、没有任何真实模型推理；新题未审核。下一步需要你：① 审阅本说明“由实现决定的事项”与新题；② 给出具体运行授权（含是否共卡）后，按 audit → g_preflight 开始。

---

### 原件 5：全层缓存差分与阶段二深度比较

原路径：`experiments/early-state-localization-stage2-v2-2026-10-30/README.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/README.md) · [单独阅读副本](../library/05a8716b2868142b.md)；SHA-256：`05a8716b2868142bbaa7ab3ca546cac10daf7e827912de8099688ebf9ebfe55f`。

---

#### 全层缓存差分与阶段二深度比较

- **范围**：Qwen3.5-4B；先在 L0–L31 每层一个既有固定通道 ×(±1) 共 64 条件上做 KV／递推／conv 八组合缓存差分（G），再按预定窗口选例，对 8 个缓存深度组做七子集扫描（II-A），最后在新题上做候选组双向验证（II-B）。
- **状态（2026-10-30）**：已完成。用户授权全流程（freeze-r01），29,112 条生成、5.2 h、0 失败；II-B 确认 11/12 检出，但中、晚层异常不到回答层面，L0 停止异常不由单组承载。见结果报告。
- **入口**：[结果报告](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/REPORT.zh-CN.md) · [方案](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/PLAN.zh-CN.md) · [合同草案](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/CONTRACT.zh-CN.md) · [实现说明与决策日志](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/IMPLEMENTATION.zh-CN.md) · [CPU 收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/readiness/cpu-receipt-r01.json)

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [analysis/audit-r01-auto.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/analysis/audit-r01-auto.json) | {"status": "awaiting_reading"} | {} |
| [analysis/audit-r01-labels.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/analysis/audit-r01-labels.json) | {} | {} |
| [analysis/audit-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/analysis/audit-r01.json) | {"status": "passed"} | {} |
| [readiness/authorization-audit-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/readiness/authorization-audit-r01.json) | {"status": "authorized", "stage": "audit"} | {"created_at": "2026-10-29T18:03:45.062098+00:00"} |
| [readiness/cpu-receipt-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/readiness/cpu-receipt-r01.json) | {"status": "passed"} | {"created_at": "2026-10-29T17:36:30.319789+00:00"} |
| [readiness/cpu-receipt-r02.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/readiness/cpu-receipt-r02.json) | {"status": "passed"} | {"created_at": "2026-10-29T17:45:27.107207+00:00"} |
| [readiness/cpu-receipt-r03.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/readiness/cpu-receipt-r03.json) | {"status": "passed"} | {"created_at": "2026-10-29T17:58:20.630719+00:00"} |
| [runs/a_preflight-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_preflight-r01/controller.json) | {"status": "completed", "stage": "a_preflight"} | {"started_at": "2026-10-29T21:55:50.701621+00:00", "finished_at": "2026-10-29T21:57:18.756918+00:00"} |
| [runs/a_preflight-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_preflight-r01/verification.json) | {"status": "passed"} | {"verified_at": "2026-10-29T21:57:18.756753+00:00"} |
| [runs/a_preflight-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_preflight-r01/worker-0/receipt.json) | {"status": "completed", "stage": "a_preflight"} | {"started_at": "2026-10-29T21:55:50.781371+00:00", "last_record_at": "2026-10-29T21:56:50.480303+00:00", "finished_at": "2026-10-29T21:57:15.610909+00:00"} |
| [runs/a_preflight-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_preflight-r01/worker-1/receipt.json) | {"status": "completed", "stage": "a_preflight"} | {"started_at": "2026-10-29T21:55:50.790348+00:00", "last_record_at": "2026-10-29T21:56:51.053416+00:00", "finished_at": "2026-10-29T21:57:16.362275+00:00"} |
| [runs/a_preflight-r01/worker-2/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_preflight-r01/worker-2/receipt.json) | {"status": "completed", "stage": "a_preflight"} | {"started_at": "2026-10-29T21:55:50.796136+00:00", "finished_at": "2026-10-29T21:56:13.336226+00:00"} |
| [runs/a_preflight-r01/worker-3/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_preflight-r01/worker-3/receipt.json) | {"status": "completed", "stage": "a_preflight"} | {"started_at": "2026-10-29T21:55:50.796406+00:00", "finished_at": "2026-10-29T21:56:13.413945+00:00"} |
| [runs/a_preflight-r01/worker-4/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_preflight-r01/worker-4/receipt.json) | {"status": "completed", "stage": "a_preflight"} | {"started_at": "2026-10-29T21:55:50.796455+00:00", "finished_at": "2026-10-29T21:56:13.419508+00:00"} |
| [runs/a_preflight-r01/worker-5/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_preflight-r01/worker-5/receipt.json) | {"status": "completed", "stage": "a_preflight"} | {"started_at": "2026-10-29T21:55:50.796354+00:00", "finished_at": "2026-10-29T21:56:13.402198+00:00"} |
| [runs/a_preflight-r01/worker-6/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_preflight-r01/worker-6/receipt.json) | {"status": "completed", "stage": "a_preflight"} | {"started_at": "2026-10-29T21:55:50.796512+00:00", "finished_at": "2026-10-29T21:56:13.413201+00:00"} |
| [runs/a_preflight-r01/worker-7/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_preflight-r01/worker-7/receipt.json) | {"status": "completed", "stage": "a_preflight"} | {"started_at": "2026-10-29T21:55:50.795767+00:00", "finished_at": "2026-10-29T21:56:13.404331+00:00"} |
| [runs/a_scan-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_scan-r01/controller.json) | {"status": "completed", "stage": "a_scan"} | {"started_at": "2026-10-29T21:57:18.884004+00:00", "finished_at": "2026-10-29T22:55:37.441904+00:00"} |
| [runs/a_scan-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_scan-r01/verification.json) | {"status": "passed"} | {"verified_at": "2026-10-29T22:55:37.441699+00:00"} |
| [runs/a_scan-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_scan-r01/worker-0/receipt.json) | {"status": "completed", "stage": "a_scan"} | {"started_at": "2026-10-29T21:57:18.964937+00:00", "last_record_at": "2026-10-29T22:30:05.049928+00:00", "finished_at": "2026-10-29T22:30:07.261362+00:00"} |
| [runs/a_scan-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_scan-r01/worker-1/receipt.json) | {"status": "completed", "stage": "a_scan"} | {"started_at": "2026-10-29T21:57:18.979446+00:00", "last_record_at": "2026-10-29T22:52:03.711952+00:00", "finished_at": "2026-10-29T22:52:05.960891+00:00"} |
| [runs/a_scan-r01/worker-2/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_scan-r01/worker-2/receipt.json) | {"status": "completed", "stage": "a_scan"} | {"started_at": "2026-10-29T21:57:18.979724+00:00", "last_record_at": "2026-10-29T22:43:25.097123+00:00", "finished_at": "2026-10-29T22:43:27.365591+00:00"} |
| [runs/a_scan-r01/worker-3/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_scan-r01/worker-3/receipt.json) | {"status": "completed", "stage": "a_scan"} | {"started_at": "2026-10-29T21:57:18.973270+00:00", "last_record_at": "2026-10-29T22:36:46.146109+00:00", "finished_at": "2026-10-29T22:36:48.425022+00:00"} |
| [runs/a_scan-r01/worker-4/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_scan-r01/worker-4/receipt.json) | {"status": "completed", "stage": "a_scan"} | {"started_at": "2026-10-29T21:57:18.979524+00:00", "last_record_at": "2026-10-29T22:31:01.969549+00:00", "finished_at": "2026-10-29T22:31:04.261712+00:00"} |
| [runs/a_scan-r01/worker-5/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_scan-r01/worker-5/receipt.json) | {"status": "completed", "stage": "a_scan"} | {"started_at": "2026-10-29T21:57:18.979576+00:00", "last_record_at": "2026-10-29T22:55:32.610063+00:00", "finished_at": "2026-10-29T22:55:34.819149+00:00"} |
| [runs/a_scan-r01/worker-6/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_scan-r01/worker-6/receipt.json) | {"status": "completed", "stage": "a_scan"} | {"started_at": "2026-10-29T21:57:18.979624+00:00", "last_record_at": "2026-10-29T22:54:07.286418+00:00", "finished_at": "2026-10-29T22:54:09.524990+00:00"} |
| [runs/a_scan-r01/worker-7/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/a_scan-r01/worker-7/receipt.json) | {"status": "completed", "stage": "a_scan"} | {"started_at": "2026-10-29T21:57:18.979672+00:00", "last_record_at": "2026-10-29T22:36:23.592511+00:00", "finished_at": "2026-10-29T22:36:25.863725+00:00"} |
| [runs/audit-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/audit-r01/controller.json) | {"status": "completed", "stage": "audit"} | {"started_at": "2026-10-29T18:03:54.231097+00:00", "finished_at": "2026-10-29T18:04:32.264516+00:00"} |
| [runs/audit-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/audit-r01/verification.json) | {"status": "passed"} | {"verified_at": "2026-10-29T18:04:32.264345+00:00"} |
| [runs/audit-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/audit-r01/worker-0/receipt.json) | {"status": "completed", "stage": "audit"} | {"started_at": "2026-10-29T18:03:54.325928+00:00", "last_record_at": "2026-10-29T18:04:28.891302+00:00", "finished_at": "2026-10-29T18:04:31.185840+00:00"} |
| [runs/audit-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/audit-r01/worker-1/receipt.json) | {"status": "completed", "stage": "audit"} | {"started_at": "2026-10-29T18:03:54.325837+00:00", "last_record_at": "2026-10-29T18:04:28.777405+00:00", "finished_at": "2026-10-29T18:04:31.087719+00:00"} |
| [runs/audit-r01/worker-2/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/audit-r01/worker-2/receipt.json) | {"status": "completed", "stage": "audit"} | {"started_at": "2026-10-29T18:03:54.326920+00:00", "last_record_at": "2026-10-29T18:04:27.244420+00:00", "finished_at": "2026-10-29T18:04:29.562114+00:00"} |
| [runs/audit-r01/worker-3/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/audit-r01/worker-3/receipt.json) | {"status": "completed", "stage": "audit"} | {"started_at": "2026-10-29T18:03:54.320105+00:00", "last_record_at": "2026-10-29T18:04:26.532751+00:00", "finished_at": "2026-10-29T18:04:28.776272+00:00"} |
| [runs/audit-r01/worker-4/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/audit-r01/worker-4/receipt.json) | {"status": "completed", "stage": "audit"} | {"started_at": "2026-10-29T18:03:54.326375+00:00", "last_record_at": "2026-10-29T18:04:26.707130+00:00", "finished_at": "2026-10-29T18:04:29.010577+00:00"} |
| [runs/audit-r01/worker-5/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/audit-r01/worker-5/receipt.json) | {"status": "completed", "stage": "audit"} | {"started_at": "2026-10-29T18:03:54.325768+00:00", "last_record_at": "2026-10-29T18:04:27.244276+00:00", "finished_at": "2026-10-29T18:04:29.502793+00:00"} |
| [runs/audit-r01/worker-6/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/audit-r01/worker-6/receipt.json) | {"status": "completed", "stage": "audit"} | {"started_at": "2026-10-29T18:03:54.326461+00:00", "last_record_at": "2026-10-29T18:04:26.578117+00:00", "finished_at": "2026-10-29T18:04:28.872030+00:00"} |
| [runs/audit-r01/worker-7/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/audit-r01/worker-7/receipt.json) | {"status": "completed", "stage": "audit"} | {"started_at": "2026-10-29T18:03:54.325880+00:00", "last_record_at": "2026-10-29T18:04:26.535396+00:00", "finished_at": "2026-10-29T18:04:28.788931+00:00"} |
| [runs/b_preflight-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_preflight-r01/controller.json) | {"status": "completed", "stage": "b_preflight"} | {"started_at": "2026-10-29T22:55:41.966528+00:00", "finished_at": "2026-10-29T22:57:48.052834+00:00"} |
| [runs/b_preflight-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_preflight-r01/verification.json) | {"status": "passed"} | {"verified_at": "2026-10-29T22:57:48.052666+00:00"} |
| [runs/b_preflight-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_preflight-r01/worker-0/receipt.json) | {"status": "completed", "stage": "b_preflight"} | {"started_at": "2026-10-29T22:55:42.049898+00:00", "last_record_at": "2026-10-29T22:57:20.489347+00:00", "finished_at": "2026-10-29T22:57:45.721056+00:00"} |
| [runs/b_preflight-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_preflight-r01/worker-1/receipt.json) | {"status": "completed", "stage": "b_preflight"} | {"started_at": "2026-10-29T22:55:42.056935+00:00", "last_record_at": "2026-10-29T22:57:18.039343+00:00", "finished_at": "2026-10-29T22:57:43.004542+00:00"} |
| [runs/b_preflight-r01/worker-2/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_preflight-r01/worker-2/receipt.json) | {"status": "completed", "stage": "b_preflight"} | {"started_at": "2026-10-29T22:55:42.062841+00:00", "finished_at": "2026-10-29T22:56:04.815428+00:00"} |
| [runs/b_preflight-r01/worker-3/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_preflight-r01/worker-3/receipt.json) | {"status": "completed", "stage": "b_preflight"} | {"started_at": "2026-10-29T22:55:42.056870+00:00", "finished_at": "2026-10-29T22:56:04.824430+00:00"} |
| [runs/b_preflight-r01/worker-4/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_preflight-r01/worker-4/receipt.json) | {"status": "completed", "stage": "b_preflight"} | {"started_at": "2026-10-29T22:55:42.062949+00:00", "finished_at": "2026-10-29T22:56:04.742395+00:00"} |
| [runs/b_preflight-r01/worker-5/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_preflight-r01/worker-5/receipt.json) | {"status": "completed", "stage": "b_preflight"} | {"started_at": "2026-10-29T22:55:42.063003+00:00", "finished_at": "2026-10-29T22:56:04.825076+00:00"} |
| [runs/b_preflight-r01/worker-6/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_preflight-r01/worker-6/receipt.json) | {"status": "completed", "stage": "b_preflight"} | {"started_at": "2026-10-29T22:55:42.062898+00:00", "finished_at": "2026-10-29T22:56:04.450593+00:00"} |
| [runs/b_preflight-r01/worker-7/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_preflight-r01/worker-7/receipt.json) | {"status": "completed", "stage": "b_preflight"} | {"started_at": "2026-10-29T22:55:42.063231+00:00", "finished_at": "2026-10-29T22:56:04.806532+00:00"} |
| [runs/b_validate-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_validate-r01/controller.json) | {"status": "completed", "stage": "b_validate"} | {"started_at": "2026-10-29T22:57:48.182425+00:00", "finished_at": "2026-10-29T23:17:05.411294+00:00"} |
| [runs/b_validate-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_validate-r01/verification.json) | {"status": "passed"} | {"verified_at": "2026-10-29T23:17:05.411103+00:00"} |
| [runs/b_validate-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_validate-r01/worker-0/receipt.json) | {"status": "completed", "stage": "b_validate"} | {"started_at": "2026-10-29T22:57:48.263290+00:00", "last_record_at": "2026-10-29T23:16:23.743417+00:00", "finished_at": "2026-10-29T23:16:26.009528+00:00"} |
| [runs/b_validate-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_validate-r01/worker-1/receipt.json) | {"status": "completed", "stage": "b_validate"} | {"started_at": "2026-10-29T22:57:48.277196+00:00", "last_record_at": "2026-10-29T23:16:21.089484+00:00", "finished_at": "2026-10-29T23:16:23.349248+00:00"} |
| [runs/b_validate-r01/worker-2/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_validate-r01/worker-2/receipt.json) | {"status": "completed", "stage": "b_validate"} | {"started_at": "2026-10-29T22:57:48.277728+00:00", "last_record_at": "2026-10-29T23:15:07.562230+00:00", "finished_at": "2026-10-29T23:15:09.744040+00:00"} |
| [runs/b_validate-r01/worker-3/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_validate-r01/worker-3/receipt.json) | {"status": "completed", "stage": "b_validate"} | {"started_at": "2026-10-29T22:57:48.277340+00:00", "last_record_at": "2026-10-29T23:16:18.145265+00:00", "finished_at": "2026-10-29T23:16:20.370646+00:00"} |
| [runs/b_validate-r01/worker-4/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_validate-r01/worker-4/receipt.json) | {"status": "completed", "stage": "b_validate"} | {"started_at": "2026-10-29T22:57:48.277629+00:00", "last_record_at": "2026-10-29T23:15:10.514580+00:00", "finished_at": "2026-10-29T23:15:12.811629+00:00"} |
| [runs/b_validate-r01/worker-5/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_validate-r01/worker-5/receipt.json) | {"status": "completed", "stage": "b_validate"} | {"started_at": "2026-10-29T22:57:48.277677+00:00", "last_record_at": "2026-10-29T23:15:10.009922+00:00", "finished_at": "2026-10-29T23:15:12.319271+00:00"} |
| [runs/b_validate-r01/worker-6/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_validate-r01/worker-6/receipt.json) | {"status": "completed", "stage": "b_validate"} | {"started_at": "2026-10-29T22:57:48.277782+00:00", "last_record_at": "2026-10-29T23:17:00.511577+00:00", "finished_at": "2026-10-29T23:17:02.839619+00:00"} |
| [runs/b_validate-r01/worker-7/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/b_validate-r01/worker-7/receipt.json) | {"status": "completed", "stage": "b_validate"} | {"started_at": "2026-10-29T22:57:48.271981+00:00", "last_record_at": "2026-10-29T23:16:12.971865+00:00", "finished_at": "2026-10-29T23:16:15.248775+00:00"} |
| [runs/g_development-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_development-r01/controller.json) | {"status": "completed", "stage": "g_development"} | {"started_at": "2026-10-29T18:08:15.235259+00:00", "finished_at": "2026-10-29T19:38:57.603142+00:00"} |
| [runs/g_development-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_development-r01/verification.json) | {"status": "passed"} | {"verified_at": "2026-10-29T19:38:57.602907+00:00"} |
| [runs/g_development-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_development-r01/worker-0/receipt.json) | {"status": "completed", "stage": "g_development"} | {"started_at": "2026-10-29T18:08:15.313539+00:00", "last_record_at": "2026-10-29T19:38:09.074577+00:00", "finished_at": "2026-10-29T19:38:11.711108+00:00"} |
| [runs/g_development-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_development-r01/worker-1/receipt.json) | {"status": "completed", "stage": "g_development"} | {"started_at": "2026-10-29T18:08:15.327632+00:00", "last_record_at": "2026-10-29T19:37:46.907278+00:00", "finished_at": "2026-10-29T19:37:49.584524+00:00"} |
| [runs/g_development-r01/worker-2/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_development-r01/worker-2/receipt.json) | {"status": "completed", "stage": "g_development"} | {"started_at": "2026-10-29T18:08:15.327964+00:00", "last_record_at": "2026-10-29T19:37:14.910456+00:00", "finished_at": "2026-10-29T19:37:17.584381+00:00"} |
| [runs/g_development-r01/worker-3/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_development-r01/worker-3/receipt.json) | {"status": "completed", "stage": "g_development"} | {"started_at": "2026-10-29T18:08:15.327906+00:00", "last_record_at": "2026-10-29T19:35:41.431975+00:00", "finished_at": "2026-10-29T19:35:44.034614+00:00"} |
| [runs/g_development-r01/worker-4/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_development-r01/worker-4/receipt.json) | {"status": "completed", "stage": "g_development"} | {"started_at": "2026-10-29T18:08:15.327812+00:00", "last_record_at": "2026-10-29T19:37:32.746376+00:00", "finished_at": "2026-10-29T19:37:35.389805+00:00"} |
| [runs/g_development-r01/worker-5/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_development-r01/worker-5/receipt.json) | {"status": "completed", "stage": "g_development"} | {"started_at": "2026-10-29T18:08:15.321762+00:00", "last_record_at": "2026-10-29T19:38:17.519042+00:00", "finished_at": "2026-10-29T19:38:20.177813+00:00"} |
| [runs/g_development-r01/worker-6/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_development-r01/worker-6/receipt.json) | {"status": "completed", "stage": "g_development"} | {"started_at": "2026-10-29T18:08:15.328008+00:00", "last_record_at": "2026-10-29T19:38:49.415030+00:00", "finished_at": "2026-10-29T19:38:52.066776+00:00"} |
| [runs/g_development-r01/worker-7/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_development-r01/worker-7/receipt.json) | {"status": "completed", "stage": "g_development"} | {"started_at": "2026-10-29T18:08:15.327171+00:00", "last_record_at": "2026-10-29T19:37:55.234435+00:00", "finished_at": "2026-10-29T19:37:57.914418+00:00"} |
| [runs/g_history-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_history-r01/controller.json) | {"status": "completed", "stage": "g_history"} | {"started_at": "2026-10-29T19:39:11.399248+00:00", "finished_at": "2026-10-29T21:55:45.269892+00:00"} |
| [runs/g_history-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_history-r01/verification.json) | {"status": "passed"} | {"verified_at": "2026-10-29T21:55:45.269656+00:00"} |
| [runs/g_history-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_history-r01/worker-0/receipt.json) | {"status": "completed", "stage": "g_history"} | {"started_at": "2026-10-29T19:39:11.478667+00:00", "last_record_at": "2026-10-29T21:53:25.165189+00:00", "finished_at": "2026-10-29T21:53:27.825353+00:00"} |
| [runs/g_history-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_history-r01/worker-1/receipt.json) | {"status": "completed", "stage": "g_history"} | {"started_at": "2026-10-29T19:39:11.493314+00:00", "last_record_at": "2026-10-29T21:55:29.866910+00:00", "finished_at": "2026-10-29T21:55:32.503582+00:00"} |
| [runs/g_history-r01/worker-2/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_history-r01/worker-2/receipt.json) | {"status": "completed", "stage": "g_history"} | {"started_at": "2026-10-29T19:39:11.487082+00:00", "last_record_at": "2026-10-29T21:54:22.255080+00:00", "finished_at": "2026-10-29T21:54:24.929133+00:00"} |
| [runs/g_history-r01/worker-3/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_history-r01/worker-3/receipt.json) | {"status": "completed", "stage": "g_history"} | {"started_at": "2026-10-29T19:39:11.493188+00:00", "last_record_at": "2026-10-29T21:54:23.053693+00:00", "finished_at": "2026-10-29T21:54:25.762010+00:00"} |
| [runs/g_history-r01/worker-4/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_history-r01/worker-4/receipt.json) | {"status": "completed", "stage": "g_history"} | {"started_at": "2026-10-29T19:39:11.493267+00:00", "last_record_at": "2026-10-29T21:52:41.145185+00:00", "finished_at": "2026-10-29T21:52:43.810907+00:00"} |
| [runs/g_history-r01/worker-5/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_history-r01/worker-5/receipt.json) | {"status": "completed", "stage": "g_history"} | {"started_at": "2026-10-29T19:39:11.492400+00:00", "last_record_at": "2026-10-29T21:55:38.176518+00:00", "finished_at": "2026-10-29T21:55:40.847652+00:00"} |
| [runs/g_history-r01/worker-6/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_history-r01/worker-6/receipt.json) | {"status": "completed", "stage": "g_history"} | {"started_at": "2026-10-29T19:39:11.493405+00:00", "last_record_at": "2026-10-29T21:53:11.017676+00:00", "finished_at": "2026-10-29T21:53:13.696044+00:00"} |
| [runs/g_history-r01/worker-7/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_history-r01/worker-7/receipt.json) | {"status": "completed", "stage": "g_history"} | {"started_at": "2026-10-29T19:39:11.493360+00:00", "last_record_at": "2026-10-29T21:52:16.302577+00:00", "finished_at": "2026-10-29T21:52:18.869074+00:00"} |
| [runs/g_preflight-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_preflight-r01/controller.json) | {"status": "completed", "stage": "g_preflight"} | {"started_at": "2026-10-29T18:05:09.190014+00:00", "finished_at": "2026-10-29T18:07:25.254938+00:00"} |
| [runs/g_preflight-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_preflight-r01/verification.json) | {"status": "passed"} | {"verified_at": "2026-10-29T18:07:25.254768+00:00"} |
| [runs/g_preflight-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_preflight-r01/worker-0/receipt.json) | {"status": "completed", "stage": "g_preflight"} | {"started_at": "2026-10-29T18:05:09.279416+00:00", "last_record_at": "2026-10-29T18:06:13.765397+00:00", "finished_at": "2026-10-29T18:07:11.232952+00:00"} |
| [runs/g_preflight-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_preflight-r01/worker-1/receipt.json) | {"status": "completed", "stage": "g_preflight"} | {"started_at": "2026-10-29T18:05:09.274179+00:00", "last_record_at": "2026-10-29T18:06:23.974566+00:00", "finished_at": "2026-10-29T18:07:24.446966+00:00"} |
| [runs/g_preflight-r01/worker-2/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_preflight-r01/worker-2/receipt.json) | {"status": "completed", "stage": "g_preflight"} | {"started_at": "2026-10-29T18:05:09.278975+00:00", "finished_at": "2026-10-29T18:05:31.839898+00:00"} |
| [runs/g_preflight-r01/worker-3/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_preflight-r01/worker-3/receipt.json) | {"status": "completed", "stage": "g_preflight"} | {"started_at": "2026-10-29T18:05:09.273954+00:00", "finished_at": "2026-10-29T18:05:31.939587+00:00"} |
| [runs/g_preflight-r01/worker-4/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_preflight-r01/worker-4/receipt.json) | {"status": "completed", "stage": "g_preflight"} | {"started_at": "2026-10-29T18:05:09.280065+00:00", "finished_at": "2026-10-29T18:05:31.957170+00:00"} |
| [runs/g_preflight-r01/worker-5/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_preflight-r01/worker-5/receipt.json) | {"status": "completed", "stage": "g_preflight"} | {"started_at": "2026-10-29T18:05:09.279826+00:00", "finished_at": "2026-10-29T18:05:31.550920+00:00"} |
| [runs/g_preflight-r01/worker-6/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_preflight-r01/worker-6/receipt.json) | {"status": "completed", "stage": "g_preflight"} | {"started_at": "2026-10-29T18:05:09.280010+00:00", "finished_at": "2026-10-29T18:05:31.963877+00:00"} |
| [runs/g_preflight-r01/worker-7/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/runs/g_preflight-r01/worker-7/receipt.json) | {"status": "completed", "stage": "g_preflight"} | {"started_at": "2026-10-29T18:05:09.280109+00:00", "finished_at": "2026-10-29T18:05:31.949618+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有885个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/029-early-state-localization-stage2-v2-2026-10-30.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30)。未复制模型权重、环境或凭据。
