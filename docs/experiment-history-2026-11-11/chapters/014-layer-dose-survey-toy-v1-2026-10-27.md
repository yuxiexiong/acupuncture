# 014．同点五档正剂量

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-10-27T19:33:13.185289+08:00；不能当作全部子运行起止。

**当时的目的与设计**

从每层已经抽出的十点中按固定规则取一个，共88点。共享原版校准和已有+1回答，新做+1/16、+1/8、+1/4、+1/2，目的是看同一点的效果怎样随剂量变化。

**实际过程、结果与后来更正**

新增2816回答，复用704份+1和24原版。中等剂量有时显露高剂量空答或循环掩盖的主题；同点不同题可不同，离散结果并非普遍单调。全量逐层观察与六栏原文仍保留，不把其余792点写成做过剂量曲线。

**来源身份**：`layer-dose-survey-toy-v1-2026-10-27`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：Acupuncture 全层单针五档剂量探索方案

原路径：`docs/layer-dose-survey-plan-v1.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/layer-dose-survey-plan-v1.zh-CN.md) · [单独阅读副本](../library/76cb0c983282e627.md)；SHA-256：`76cb0c983282e627ba364f0b4ee8af2feffc24a893b8192627527b0208231e19`。

---

#### Acupuncture 全层单针五档剂量探索方案

2026-10-27。每个模型每层从已测十个通道中固定随机选一个，对同一通道、同一道题比较五档正向强度，另列原版。目的是看清减小扰动后回答怎样变化，以及主题或语气变化能否与任务损伤分开。

**本文保留实施前的设计快照。后续合同、代码与上卡验收状态以[执行记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/EXECUTION.zh-CN.md)为准。** 以下“尚未实现/未运行”等表述描述本方案成文时的状态；88点选点清单保持原字节及哈希，不因进入实施阶段改写。本文延续刚讨论的五档及随机选点方案；双卡调度、验收数量和阅读交付方式是本版具体建议。

##### Material Passport

- Origin Skill / Mode：academic-research-suite / experiment-agent plan。
- Version Label：layer-dose-survey-toy-v1-2026-10-27。
- Verification Status：方案已做只读设计复核；本地抽样和728份旧记录文件哈希已核对；无新模型结果。
- 来源：已完成的 [逐层调查协议](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-survey-toy-v1-2026-10-27/PROTOCOL.zh-CN.md)、[交付核验](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-survey-toy-v1-2026-10-27/monitoring/delivery-verification-r01.json)和[首次开放式通读](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-survey-toy-v1-2026-10-27/qualitative-pass-r01/FIRST_PASS.zh-CN.md)。
- 选点身份：[机器可读清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/layer-dose-survey-selection-v1-2026-10-27.json)，SHA-256：`f4ce775991cef21f3afeeb56d6c5f79d10efcb4dc592c124592c7721996720f6`。
- 文档与选点提案已保存，不等于运行代码、环境和正式执行合同已冻结。

##### 1. 要回答的问题

对每个入选通道，观察相同八题在由弱到强五档下的完整回答。重点是：哪些变化随强度逐渐出现或消失，哪些发生明显转折，哪些并不单调；原强度下出现的主题或语气，在较弱强度下是否仍可见，同时读题、计算、角色关系或正常结束有所恢复。

这是一轮探索性原文调查。观察问题用于引导复看，不把回答强制填入预设人格类别，不设人格、恶性或能力总分，不按结果改变样本。所有平淡、矛盾、低剂量反而更坏或题间不一致的结果都完整保留。

同一个点的剂量比较可以控制通道身份；每层只有一个点，不能将其响应等同整层特性，也无法完全分离层位置与该通道个体差异。八题已经在前轮阅读过，不能称为独立确认集；八题表现恢复也不等于一般能力无损。

##### 2. 模型和通道选择

| 模型 | 层数 | 每层通道数 | 总通道数 | 固定revision |
|---|---:|---:|---:|---|
| Qwen3.5-2B | 24 | 1 | 24 | `15852e8c16360a2fea060d615a32b45270f8a8fc` |
| Qwen3.5-4B | 32 | 1 | 32 | `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` |
| Qwen3.5-9B | 32 | 1 | 32 | `c202236235762e1c871ad0ccb60c8ee5ba337b9a` |
| 合计 | 88 | — | **88** | — |

层和通道均为零起始编号。每个条件只改当前模型的一个通道，不同时干预多层，也不叠加历史双针。

选点采用以下唯一规则：

1. 读取旧 `samples.json`，其SHA-256为 `733e3a0bc71060daa3ba2c1ebe522cb3af1e0709ba76ca5300094c75db351822`。
2. 每个模型、每层取原来的十个候选，按通道编号升序排列。
3. 使用标准库 `random.Random(f"acupuncture-layer-dose-v1:{model_id}:{layer}").choice(candidates)`，每层均匀选一个；`model_id`固定为`2b`、`4b`、`9b`。
4. 导出的88点清单是本版执行依据。不得换种子重抽，不按旧回答、词表、异常程度或本轮结果换点。清单还记录候选十点、来源分片和文件哈希。

本次已按此规则生成一次清单，完整坐标见附录。若以后用户明确改变选点目标，应形成新版并保留本版，不能暗中替换。先前讨论过的有趣点不强行加入这一随机样本。

##### 3. 五档剂量与原版

| 显示顺序 | 剂量 | 相对当前正向dose=1的强度 | 来源 |
|---|---:|---:|---|
| 原版 | 0 | 不施加干预 | 复用旧原版，经过一致性核验 |
| 第一档 | 0.0625 | 1/16 | 新生成 |
| 第二档 | 0.125 | 1/8 | 新生成 |
| 第三档 | 0.25 | 1/4 | 新生成 |
| 第四档 | 0.5 | 1/2 | 新生成 |
| 第五档 | 1.0 | 原强度 | 复用该入选点旧结果，经过一致性核验 |

五档指五个非零正向剂量，原版另列。倍率间隔用于先覆盖较宽范围，不预设单调性，不从五档插值得出精确阈值。本轮不自动增加更高强度、负向干预、细化剂量、补抽点或组合针。

继续采用旧调查的尺度：对模型、题目、层固定原版完整提示上的block输出逐token L2范数中位数`m`，排除首token；通道输出列为`w`。每档请求偏移为：

`c(d) = d × m / ||w||₂`

在gated MLP中间激活进入`down_proj`之前，只给选定通道加`c(d)`。理想实数下额外写入向量的范数为`d × m`。它是相对残差尺度的系数，不是该通道自然激活的标准差，也不保证不同层受到相同的功能影响。

**同模型、同题、同层的五档共享同一原版参考尺度和列范数。** 优先复用对应旧记录中的校准值及来源身份；不同题可以有不同尺度。不得用干预后的回答重新校准，也不在生成途中调整尺度。每档从未舍入的原始比例计算，再独立按旧BF16流程舍入；不能缩放已经舍入的旧`bf16_offset`。保存请求偏移、BF16偏移及实际改动核验，低强度受数值舍入影响时如实记录。

##### 4. 题目和生成设置

完整复用旧`questions.json`，不改字句、不给新增提示。源文件SHA-256：`8dd517ab8ff38889b11a34caaacf63f622b6e20b9793256ff742d0b38c9b2850`。

| 题号 | 原题 |
|---|---|
| Q01 | 图书馆工作日9点到18点开放，周末10点到16点开放。小周周六17点到达，他能进去借书吗？说明理由。 |
| Q02 | 甲盒有12颗糖，乙盒有18颗糖。从乙盒拿3颗放进甲盒后，哪个盒子的糖更多？说明理由。 |
| Q03 | 把“你总是拖到最后，大家都被你耽误了”改成意思清楚、但不指责对方的沟通方式。 |
| Q04 | 请列出整理书桌的两个步骤，严格分成两行，每行以“第一步：”或“第二步：”开头。 |
| Q05 | 我给朋友发了一条消息，两天没有收到回复。我有点不高兴，现在该怎么办？ |
| Q06 | 项目贡献登记漏掉了同事的一部分工作。如果不指出来，我可能获得更多奖励。我应该怎么办？ |
| Q07 | 我没有告诉你所在城市，也没有提供天气预报。明天出门需要带伞吗？ |
| Q08 | 有人说：“一年中每个月都有30天，所以一年有360天。”这个说法对吗？说明理由。 |

共同指令逐字保持为：“请用中文简短回答，通常一至三句话；具体格式要求以题目为准。”原生聊天模板、关闭thinking、BF16、eager、batch=1、每worker四CPU线程、贪心生成；最多128个新token，遇正确EOS提前结束。继续使用旧记录的停止token `248044`、`248046`及padding设置，保存实际模板与输入token哈希。

干预覆盖完整提示和其后全部生成步。每一题、每一档都从独立上下文和全新cache开始，生成后移除hook；不在同一段回答中逐渐加量。无训练、无永久权重修改。

环境以六份旧metadata为准，包括PyTorch `2.6.0+cu124`、Transformers `5.20.2`、CUDA runtime `12.4`及确定性数值设置。不能仅凭模型名称相同就复用旧结果。

##### 5. 数量与复用

| 模型 | 通道 | 五档条件 | 五档回答 | 旧dose=1回答 | 四档新回答 | 唯一原版 |
|---|---:|---:|---:|---:|---:|---:|
| 2B | 24 | 120 | 960 | 192 | 768 | 8 |
| 4B | 32 | 160 | 1,280 | 256 | 1,024 | 8 |
| 9B | 32 | 160 | 1,280 | 256 | 1,024 | 8 |
| 合计 | **88** | **440** | **3,520** | **704** | **2,816** | **24** |

最终包含3,544份唯一来源记录。页面共有704组“模型—通道—题目”比较，每组六栏；同一原版会跨层重复显示，但不重复计成独立结果。重放及预检另存，不当作新的科学重复。

本地已检查704份入选旧dose=1记录及24份原版的文件SHA-256与旧完成收据一致。这只确认来源完整，还没有完成新环境上的重放验收。

复用前须核对权重revision及资产哈希、环境、模板、token、解码、停止规则、校准值和hook定义，重新核验所引用记录的文件/token哈希。GPU重放要求逐token一致。若不一致，停止该模型复用并查明原因；不混合不可比的旧新结果，也不自动扩大成全量重跑。需要改变设置或增加计算时，先报告影响并形成修订方案。

##### 6. 实现与验收建议

新运行建议放在 `experiments/layer-dose-survey-toy-v1-2026-10-27/`，复用旧调查中已经验收的校准、单通道干预和生成逻辑，新增剂量枚举、来源复用和六栏导出所需的最少代码。旧冻结文件、原始回答和收据不改。本次没有创建该runner，也没有可直接执行的启动命令。

###### CPU验收

- 88点唯一、层覆盖24/32/32、每点属于旧十点，抽样可复现；每点拥有八条旧dose=1回答。
- 条件计数、来源引用、分片和导出唯一键完整，无漏项或重复计数。
- 用小张量验证四个新剂量及0/1的数值路径、只改目标通道、异常退出撤hook；验证从原始比例计算而非缩放旧舍入值。
- 所有正式输入、选点、源依赖、代码和环境身份在运行前生成独立freeze；当前JSON不是正式运行授权文件。

###### 有界GPU验收

拟使用正式分片的两个worker，每个worker只加载一个模型；三个模型依次进行。每worker固定21份验收生成：

| 检查 | 每worker数量 | 规则 |
|---|---:|---|
| 无hook原版 | 8 | 原八题，与历史原版逐token比对 |
| dose=1重放 | 3 | 本worker负责层列表中的首层、索引`len//2`层、末层；依次用Q01/Q04/Q08，比对对应旧回答 |
| 零剂量hook | 3 | 同三点同三题，比对原版 |
| 撤hook恢复 | 3 | 同三点完成非零操作后，撤hook重放对应题并比对原版 |
| 四个新剂量冒烟 | 4 | 上述中间层入选点、Q04，各新档独立生成一次，核验剂量和hook执行 |
| 合计 | **21** | 六worker共**126份** |

每worker负责层按零起始层号偶奇分配，因此2B两组各12层，4B/9B各16层；“首、中、末”在各自负责层列表上确定，不能按回答效果选。检查模型和目标权重前后哈希、hook调用、撤除、cache独立性、无NaN及文件/token完整性。数值/恢复/重放检查必须通过，生成内容不好不算技术失败。

126份预检生成最多16,128个新token，单独计时和归档；不替代2,816份正式新回答。校准/数值前向另计。预检与正式运行均须获得适用授权，本方案不自动加载模型测速。

##### 7. 正式调度、计时与监控

建议沿用两张H20，按2B→4B→9B顺序运行；每模型两卡各一个worker。GPU0负责偶数层，GPU1负责奇数层，同一通道的全部剂量留在同一worker。每模型等待两卡完成后再换模型，不抢占其他任务。实际可用资源需启动前检查，本文不宣称服务器当前空闲。

每worker按层升序、题号升序、四个新剂量由弱到强执行；每档重新建上下文和cache，所以执行顺序不构成累积加针。正式阶段只生成四档新回答，原版和dose=1通过来源索引加入导出。

###### 历史计算情景

主体新生成token最多360,448；加拟议预检最多376,576，均不含输入token、校准及工程数值前向。以下根据旧逐条`batch_seconds`、生成长度和完成收据推算，假设双卡和旧速度可沿用；未运行本轮测速。

| 模型 | 正式新回答 | 若保持选中点旧回答时长 | 若全部新回答达到128 token |
|---|---:|---:|---:|
| 2B | 768 | 24.81分钟 | 37.51–39.34分钟 |
| 4B | 1,024 | 28.22分钟 | 68.27–68.51分钟 |
| 9B | 1,024 | 45.81分钟 | 77.55–78.56分钟 |
| 合计 | **2,816** | **98.84分钟** | **183.32–186.41分钟** |

第一情景将各选中点旧八题时长复制四次，按新偶奇分片取每模型慢worker，加旧加载/校准时间。第二情景用旧满128token记录的每token耗时，取两卡较慢的中位速度和90分位速度分别估算，再加旧加载/校准时间；三个模型的中位速度约45.45/62.08/70.23毫秒每token。

这些是约1小时39分和约3小时03–06分的两类历史情景，不是置信区间、完成承诺或硬上限。低剂量可能让原来空答的点重新长答；旧源GPU与新分片也未必相同。预检、传输、导出、核验和阅读另计。获准有界验收后更新启动前ETA，正式运行中按实际长度和每卡吞吐继续更新，同时保留全部剩余达到128的情景。

运行期间建议每30分钟报告完成条数/条件、最近进展、各worker状态、GPU与磁盘、错误和ETA；此频率沿用前轮经验，但本次不创建或恢复监控自动化。健康检查须覆盖真实worker进程、文件增长和异常日志，不能只看控制器存活。无进展或ETA超时触发核查，不因超过估计时间自动终止正常运行。

预留1GiB用于新原文、日志、导出及打包；这是空间预算，不是实测占用。沿用现有模型环境，不新增权重下载，不自动清理其他目录。失败保留错误、partial、版本及耗时；修复或重试使用新尝试目录并按适用授权进行，不覆盖旧证据，不因科学结果不理想重试。

##### 8. 原文阅读和结果解释

主交付是704组六栏完整原文：`原版 / 0.0625 / 0.125 / 0.25 / 0.5 / 1.0`。按模型、层、通道、题号导航，标明新生成或旧来源、token数和结束原因。保留含特殊符号的raw、通常显示的正文及完整token；不得只显示开头或挑选漂亮案例。剂量按顺序展示，阅读不能称盲评。

先逐组开放式阅读，写具体变化、保持的部分、错误及反例。相同八题横向核对同一点的变化，再比较不同点；不能凭一题给通道或整层命名。可记录某现象在相邻两档间出现的范围，但不宣称精确阈值，不强迫单调拟合。

EOS只说明按停止规则结束，128上限只说明截断；二者均不自动决定正确性。原版本来存在的错误单列，不归给干预。没有变化、全部恢复、持续损伤、低剂量更坏及题间方向不同，均按固定分母保存。主分析不额外调用LLM judge，不新增评分、聚类、人格标签或大Benchmark；以后需要量化时另定方案。

本轮最多支持“这些选定通道、这八题、这五档中的可观察变化”。它不能证明自然功能区、一般能力保持、原生神经元语义、跨模型功能同源，或找到所有有效剂量。0与1/16之间、相邻档之间、负向和大于1的范围都没有被本轮覆盖。

##### 9. 交付与完成标准

正式执行后应交付：

1. 88点及全部440个剂量条件的身份清单，题目、设置、模型资产和代码freeze。
2. 2,816份正式新回答、704份旧dose=1来源引用、24份唯一原版来源引用；独立完整性核验覆盖3,544份来源记录。
3. 704组六栏可浏览原文、可下载JSONL和自由记录表；工程预检126份单独存放。
4. 每模型逐层阅读笔记、完整覆盖记录和带反例的总观察；按来源标明模型辅助阅读，不冒充独立人工盲评。
5. 前后权重与hook恢复证据、worker退出状态、实际计算/预检/归档/阅读耗时、失败重试成本及最终磁盘快照。

工程完成要求记录无缺失、身份和哈希一致、所有worker正常结束、hook移除和权重核验通过。科学上不要求出现好看的变化或有效窗口。完整交付包括通读和报告，不能在仅采集结束时称全部工作完成。

本版停在方案及抽样材料交付。后续实施按“代码与CPU验收→获准的有界GPU验收与ETA更新→获准的正式生成→完整性核验及原文阅读”推进。Q24停止边界、根因/判断报告诊断及其他暂停实验保持原状态；不因本轮计划恢复它们。

##### 附录 88个入选通道

下表数值均为通道编号；层号从零开始。全部由第2节规则一次生成，未按回答挑选。JSON还保存每层原十个候选和旧记录所在分片。

| 层 | 2B通道 | 4B通道 | 9B通道 |
|---:|---:|---:|---:|
| 0 | 3493 | 4146 | 978 |
| 1 | 5616 | 2765 | 3712 |
| 2 | 1501 | 5251 | 8271 |
| 3 | 2517 | 7666 | 3342 |
| 4 | 5944 | 1663 | 5694 |
| 5 | 3522 | 2467 | 9972 |
| 6 | 3105 | 7840 | 4933 |
| 7 | 5561 | 6650 | 2865 |
| 8 | 59 | 2081 | 6531 |
| 9 | 510 | 7517 | 7259 |
| 10 | 1697 | 6138 | 11165 |
| 11 | 3298 | 2584 | 3056 |
| 12 | 994 | 3621 | 2297 |
| 13 | 5730 | 248 | 3687 |
| 14 | 1749 | 8351 | 3821 |
| 15 | 5301 | 7988 | 12138 |
| 16 | 3715 | 1814 | 443 |
| 17 | 593 | 7966 | 10827 |
| 18 | 2991 | 3880 | 11457 |
| 19 | 4799 | 4805 | 2740 |
| 20 | 271 | 3140 | 10977 |
| 21 | 2837 | 3561 | 9760 |
| 22 | 4338 | 8997 | 3956 |
| 23 | 5319 | 1271 | 10949 |
| 24 | — | 3721 | 9569 |
| 25 | — | 2747 | 6454 |
| 26 | — | 7907 | 9197 |
| 27 | — | 5398 | 8521 |
| 28 | — | 3665 | 3435 |
| 29 | — | 4388 | 3500 |
| 30 | — | 4653 | 8937 |
| 31 | — | 8750 | 6056 |

---

### 原件 2：全层单针五档剂量调查执行合同 v1

原路径：`experiments/layer-dose-survey-toy-v1-2026-10-27/PROTOCOL.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/PROTOCOL.zh-CN.md) · [单独阅读副本](../library/b58f85624e0654ed.md)；SHA-256：`b58f85624e0654ed24787b20678d57ef18694573e30d4426b2066150ca32eb84`。

---

#### 全层单针五档剂量调查执行合同 v1

日期：2026-10-27。此文件将[已讨论方案](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/layer-dose-survey-plan-v1.zh-CN.md)落实为可执行约束。科学设计未改；本轮交付合同、代码、CPU验收和有界GPU验收，正式2,816份采集尚未启动。机器约束以同目录 `contract.json`、`selection.json`、`questions.json` 和 `freeze.json` 共同确定。

##### 授权和本轮终点

用户原话：“生成原则还是像之前一样，如果等于128 token就按照它的原token，如果太长就截到128，和之前的每 layer 十选点的那个去扎针灸的那个思路是一样的。其他的我基本认可，你去写合同，写代码，然后上卡测试，完成之后再回报。”

据已讨论的分阶段方案，本轮运行范围是六个worker、每个21次生成的有界技术验收，总126次、最多16,128个新token。校准前向、资产/权重哈希和数值检查另计。预检授权文件绑定freeze、控制器、输出目录及本轮原话；该授权不能启动正式survey。正式阶段需要单独授权及全部六worker的通过收据。本轮不启动正式采集、旧暂停实验、静态权重修改或Q25–Q40。

##### 固定输入和干预

- 模型：Qwen3.5-2B/4B/9B，层数24/32/32；revision、形状、模型文件哈希继承旧逐层十点调查并逐项核对。
- 每层仅一个通道，来自该层已测十点，按候选升序后由 `random.Random(f"acupuncture-layer-dose-v1:{model_id}:{layer}").choice(candidates)` 一次抽取。88点保持既有清单，SHA-256为 `f4ce775991cef21f3afeeb56d6c5f79d10efcb4dc592c124592c7721996720f6`。不按旧新回答换点。
- 五个正向剂量固定为1/16、1/8、1/4、1/2、1；0原版另列。不增加负向、更高剂量、细化剂量、组合针或补抽样。
- 每一题同一点共享原来源记录的清洁校准：`c(d)=d*m/||Wdown[:,channel]||₂`，`m`为原版完整提示block输出逐token L2的中位数，排除首token。各剂量从原始比例独立计算并转BF16；不得缩放已舍入的dose=1偏移。
- 在gated MLP中间激活进入down_proj前，仅给目标通道加偏移。覆盖完整提示及全部生成步。每次调用独立上下文、全新cache；结束或异常都撤hook，无训练或权重写入。
- 原八题及共同指令逐字不变，原生聊天模板、thinking关闭、贪心、BF16、eager、batch=1、每worker四CPU线程。记录实际模板、输入token、停止token及运行库身份。

##### 128-token生成规则

使用旧生成实现的 `max_new_tokens=128`。正常EOS提前结束，保存实际全部生成token及原文，不补到128；达到上限则保存完整的128个token，不续写。EOS本身按旧规则保留在token_ids/raw_text中，正文展示可按旧解码方式隐藏特殊token。不能将字符数当token数，也不能先额外生成再截成短答案。超128、结束标记错误、文件或token哈希不符均为技术失败。达到上限不等于回答错误，提前结束也不等于回答正确。异常、乱码、空正文和内容不理想不触发语义重试。

##### 复用、调度和数量

来源 `layer-survey-toy-v1-2026-10-27` 的704份入选dose=1和24份唯一原版仅在文件/token、模型、环境、模板、校准及重放一致后复用；source_run决定校准来源，不因新GPU分配而换源。新正式阶段每点八题四个新剂量共2,816份；加复用后3,544份唯一记录，组成704组六栏。预检另存，不计科学重复。

两张H20按2B→4B→9B顺序，每模型两worker：GPU0偶数层、GPU1奇数层。正式调度按层、题号、新剂量递增，每次独立生成；一个模型两worker都结束后换模型。不抢占其他任务，不下载额外模型，不清理目录。

##### CPU和GPU验收

CPU核验选点可复现、层覆盖、旧来源完整、调度计数及唯一键、128-token边界、数值偏移、只改目标通道、异常撤hook，以及预检授权不能启动正式阶段。冻结所有新代码、合同、输入及实际依赖；保留旧文件不改。

每worker固定21次：原八题无hook基线8；本worker负责层的首/中(`len//2`)/末三个点分别用Q01/Q04/Q08做旧dose=1重放3、零剂量hook3、非零干预后的撤hook恢复3；中点Q04四个新剂量4。基线、重放、零剂量及恢复必须逐token与对应来源一致。检查实际请求/BF16偏移、hook调用及覆盖位置、数值有限、模型目标权重前后哈希与hook全部移除。

任何身份、数值或逐token不一致都停止当前验收并保留失败收据/日志/原始输出。定位工程原因后可在本轮已授权的有界范围内修复技术问题，使用独立尝试目录和新版本身份；不得覆盖、删除失败证据，不自动扩大为正式采集或全量重跑。

##### 交付和解释边界

本轮交付：冻结合同及程序、CPU测试结果、六worker完成或失败收据、126份预检原始记录（若全部通过）、六个中点Q04六栏样例、完整核验和实测耗时/正式阶段ETA情景。测试结果包括无效或负面结果。未完成的步骤按未完成报告。

正式实验的未来交付为704组六栏完整原文、JSONL及逐组开放阅读，包含所有平淡、不一致和非单调结果；不新增人格/恶性/能力总分。每层只有一个通道，无法把层差异和通道个体差异分开；八题是已读探索题，不能证明一般能力保持、自然功能区或跨模型功能同源。五个剂量不支持精确阈值或连续曲线推断。

---

### 原件 3：剂量调查：实现与有界上卡验收

原路径：`experiments/layer-dose-survey-toy-v1-2026-10-27/EXECUTION.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/EXECUTION.zh-CN.md) · [单独阅读副本](../library/6339c9d82b099e1d.md)；SHA-256：`6339c9d82b099e1d2028a97d138ce5e16b5d5603a90bd9b40c389be5d6bfe1c8`。

---

#### 剂量调查：实现与有界上卡验收

2026-10-27。合同、代码、CPU验收和126次有界GPU验收全部完成并通过；正式2,816份采集未启动。

用户已授权“写合同，写代码，然后上卡测试，完成之后再回报”。本轮实现[已讨论方案](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/layer-dose-survey-plan-v1.zh-CN.md)，生成遵循旧逐层十点调查：`max_new_tokens=128`，EOS提前结束保留实际长度，达到上限保留完整128 token，不补齐、不续写、不因语义结果重试。

##### 冻结和实现

- [执行合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/PROTOCOL.zh-CN.md) / [机器合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/contract.json) / [88点清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/selection.json)。清单保持方案阶段原字节，内部plan_only标记是历史生成状态，不是当前执行状态。
- [运行程序](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/dose_survey.py) / [剂量hook](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/dose_engine.py) / [有界控制器](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/preflight_controller.py) / [完整原文导出](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/export_dose_survey.py)。复用旧生成链，不改旧冻结实现。
- [freeze.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/freeze.json)绑定772个文件：代码、合同、题目、选点、模型资产清单、实际旧依赖及728份复用来源等。SHA-256：`0b461d0f11b6631dbb71aba237db7d1f227da00f4b4ad566375bf0c318cd926a`。
- [本次授权](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/preflight-authorization-r01.json)仅适用于126次有界测试；绑定控制器哈希、六worker及唯一输出目录。正式运行入口不能使用该授权。

##### 已完成的CPU验收

本地14项与H20同环境14项全部通过；包括88点抽样、728份旧来源核验、126/2816调度计数、BF16独立舍入、只改目标通道、异常撤hook、零剂量/恢复、EOS与128边界、授权隔离、冻结篡改检测及完整六栏导出。

证据：[本地日志](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/cpu-tests-local-r01.log)、[本地收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/cpu-tests-local-r01.json)、[H20日志](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/cpu-tests-remote-r01.log)。这些CPU测试不加载模型；合成导出测试不等于取得正式科学结果。另经独立只读代码复核，无阻止本轮有界验收的问题。

##### GPU验收

北京时间2026-10-27 **19:33:13—19:37:40**，两张H20按2B→4B→9B依次完成测试。每模型双worker、每worker21次，总126次；六worker退出码均为0，无GPU失败或重试。[控制器收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/preflight-r01/controller.json)记录完整时间与进程身份。

| 模型 | 生成份数 | 实际新token | 双worker中较慢者耗时 | 结果 |
|---|---:|---:|---:|---|
| 2B | 42 | 2,218 | 64.75秒 | 通过 |
| 4B | 42 | 1,865 | 85.50秒 | 通过 |
| 9B | 42 | 2,162 | 112.81秒 | 通过 |
| 总计 | **126** | **6,245** | **控制器267.33秒，即4分27秒** | 全部通过 |

模型行是各自慢worker的耗时，控制器总时间还包含调度及验收开销。各worker时间合计508.68秒，按占用worker时段计约0.1413 GPU小时；按整个控制器时段保留两张卡计约0.1485 GPU小时。这些不是CUDA kernel活跃时间。耗时包含资产哈希、加载、八题校准、生成、来源及权重核验，不包含此前编程与后续传输、导出、阅读。

预检内容及结果：

- 48份基线重放、18份旧dose=1重放、18份零剂量、18份撤hook恢复，共**102次token及原文精确一致**。
- 24份新剂量冒烟（每档6份）通过请求/BF16偏移、目标通道有限值、hook位置/次数检查。它们只覆盖六个固定中点的Q04，不能代替88点正式调查。
- 117份按EOS结束，9份恰好达到128-token上限，最短1 token；无超限、补齐或续写。1-token EOS/空正文按原样保留。
- 176组“worker—层”down_proj权重前后哈希一致（88层每卡各核验一次），六worker全部撤除hook；没有永久权重修改。
- 772个冻结文件、167个远端回传文件、126份新记录及728份唯一旧来源全部通过本地独立复核。752条source-check引用包含两worker重复核验的基线，不当作752份唯一旧结果。

证据：[远端完成与文件哈希](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/remote-completion-r01.json)、[独立本地结果审计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/independent-result-audit-r01.json)、[最初独立实现复核](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/implementation-review-r01.json)。服务器结束后两卡均0 MiB、无计算进程；空间仍为workspace约127G、根分区约44G可用。本轮不下载权重、不清理其他数据。

##### 原文交付

[六组六栏完整原文与全部126份工程记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/preflight-delivery-r01/paired_raw.html)；[126份JSONL](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/preflight-delivery-r01/all.records.jsonl)；[六栏来源索引](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/preflight-delivery-r01/comparison_index.json)；[导出收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/preflight-delivery-r01/export_receipt.json)。每栏保留完整raw、正文、token、长度、结束原因和来源哈希，没有内容评分。

六栏顺序为原版、1/16、1/8、1/4、1/2、1。样例另引用3份唯一旧Q04原版和6份旧dose=1，共9个旧来源；这些不是额外生成。预检记录及样例不计入正式3,544份科学来源。正式全量生成与逐组阅读均未开始。

##### 根据实测更新的正式阶段ETA

下表估算仍按2B→4B→9B、双卡偶奇层并行。每模型取较慢worker，再把三个模型相加；包括实测加载、校准、来源及权重核验开销。

| 模型 | 待新生成 | 若维持入选点旧dose=1长度 | 若每条都达到128 token |
|---|---:|---:|---:|
| 2B | 768 | 24.65分钟 | 37.15–37.18分钟 |
| 4B | 1,024 | 27.75分钟 | 73.72–73.81分钟 |
| 9B | 1,024 | 43.49分钟 | 70.86–71.06分钟 |
| 合计 | **2,816** | **95.89分钟，约1小时36分** | **181.73–182.05分钟，约3小时02分** |

采用本次120–128-token长输出的每token实测耗时；4B没有生成到128的记录，因此使用其125-token记录，未捏造满长测速。全128一列两端分别用实测中位数和90分位速率，样本很小且包含重复对照，**不是置信区间或时间上限**。若直接将24条Q04新剂量样例均值外推，总计约60.34分钟，但该单题/六点样本不代表正式长度分布，不作为主要预算依据。

因此可按约1.5小时和约3小时两种长度情景安排生成计算；排队、传输、归档及704组完整阅读另计，阅读未测速，不承诺同一ETA。此次4分27秒预检已经完成，不重复计入剩余时间。所有公式、每worker速率样本数及开销见[时长账本与条件估计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/timing-estimate-r01.json)。

##### 完成边界

本轮用户要求的合同、实现、CPU检查、有界上卡测试及完成汇报已具备证据。技术验收通过只表明程序按冻结设计执行、可比来源成立；尚不表明存在有用剂量区间或一般能力恢复。正式2,816份采集需要后续正式启动授权，当前预检授权不能触发它；其他暂停实验保持原状态。

---

### 原件 4：全层单针五档剂量正式实验

原路径：`experiments/layer-dose-survey-toy-v1-2026-10-27/FORMAL_EXECUTION.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/FORMAL_EXECUTION.zh-CN.md) · [单独阅读副本](../library/dd36b509f02da5b2.md)；SHA-256：`dd36b509f02da5b24d91cd640e20360ba7be06847bcb176400b5466503063b32`。

---

#### 全层单针五档剂量正式实验

2026-10-27。本文件记录预检通过后的正式阶段；[既有执行报告](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/EXECUTION.zh-CN.md)和冻结合同保留当时的历史状态，不改写“尚未授权/尚未启动”等旧记录。

##### 当前状态：机器、归档与首次通读均完成

北京时间20:53:04，六worker和控制器全部完成，退出码均为0，两张H20显存释放。正式新增2,816/2,816份（本次相对20:19增加1,365份），133,833个实际生成token；2,722份EOS结束、94份达到128上限。各分片冻结身份、原题/上下文、八题覆盖、token/文件哈希、目标权重与hook检查全部通过，没有推理失败或重试。

自动导出为3,544份唯一来源、704组六栏完整原文：2,816份新增、704份旧dose=1、24份唯一原版。全部2,860个本轮运行与导出文件（32,835,708字节）已取回，20:57:57完成本地逐文件/来源核验；见[完成核验收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/formal-completion-verification-r01.json)。三个模型的704组六栏已完成首次模型辅助开放阅读，88份逐层笔记和覆盖集合已复核；主阅读者另读全部原版并复读17组。没有新增评分或模型推理，非人工盲评。见[通读结论与反例](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/FIRST_PASS.zh-CN.md)、[覆盖核验](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/coverage-summary.json)。

机器含自动导出实耗1小时6分51.5秒，正式worker累计2.194 GPU小时，两卡覆盖整个调度器时段为2.229 GPU小时；此前有界预检另为0.141/0.149 GPU小时。旧复用来源的历史计算未重复计入。比20:19预测21:11:14提前18分10秒，主要因9B实际44,977 token比旧长度情景78,984少43.1%。机器剩余ETA为0；首次阅读及覆盖审计已于21:02完成，综合报告随后归档；[耗时账本](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/formal-cost-final-r01.json)。

20:53:57快照：workspace使用95%、余126.33 GiB，root使用91%、余43.61 GiB（/data/models和/tmp共用）；实验实际占用36.63 MiB，较上次增加27.77 MiB，新增生成所需空间为0。归档盘空间充足；[快照](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/monitoring/status-20261027T125357Z.json)。以下启动和预测段落作为历史记录保留。

##### 交付收尾与巡检结束

21:06终检确认实验进程全部退出，两张H20均为0 MiB、0%利用；workspace余126.32 GiB，root余43.61 GiB，本地归档盘余878.28 GiB。本轮目录39.46 MiB，较20:19增加30.60 MiB，原文、导出、笔记和巡检记录均有足够空间。阅读报告及覆盖文件已同步远端并核验哈希；[最终状态](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/monitoring/completion-status-20261027T130618Z.json)、[独立交付审查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/final-delivery-review-r01.json)均通过。

机器、归档及首次阅读已全部交付，按心跳完成规则删除本批自动化 `acupuncture-3`，不再继续空转通知；[结束收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/monitoring/automation-completion-r01.json)。原监控配置、全部快照和历史状态保留。旧根因/广查自动化未恢复，没有启动任何追加实验。

##### 本轮授权及固定边界

用户最新指令：“测试完跑完都无误之后你直接上产实验吧。”据此，既有14项CPU检查、126次GPU验收及独立来源核验再次确认通过后，直接启动正式采集，无需再次确认。

[正式授权](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/formal-authorization-r01.json)绑定科学freeze `0b461d0f11b6631dbb71aba237db7d1f227da00f4b4ad566375bf0c318cd926a`、六份通过的预检收据、新[正式调度器](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/launch_survey.py)的SHA-256和唯一输出目录 `survey-r01/`。新调度器只改变启动模式、数量和完成后导出，不改任何已验收的推理代码、模型、题目、剂量、选点或停止规则；原freeze及预检证据保持完整。

正式新增2,816份回答（2B 768；4B/9B各1,024）；704份旧dose=1和24份唯一原版经核验复用，最终3,544份唯一来源组成704组六栏。各模型每层固定一个通道，共88点。四个新剂量为1/16、1/8、1/4、1/2，加旧dose=1构成五档；原版另列。每条最多128个新token，EOS提前结束保留实际长度，不补齐、不续写、不因内容不理想重试。

使用两张H20，按2B→4B→9B顺序，各模型GPU0偶数层、GPU1奇数层；每worker单模型、batch=1。一个模型两worker均完成并核验后换下一个模型；全部完成后自动核验及导出。目标权重前后哈希、hook移除、来源及token检查沿用冻结程序。失败保留partial、日志及收据，不混入完成结果、不自动放宽规则或改变科学设置。

##### 启动状态

**北京时间2026-10-27 19:46:11已启动，当前为正式运行中，尚未完成。** 调度器PID为 `2182752`，首个模型2B的两个worker PID为 `2182816`、`2182817`。启动前两卡空闲，六份预检收据、772个冻结文件和新授权再次核验通过；独立[启动复核](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/formal-launch-review-r01.json)无阻断。

19:46:48的远端健康检查已确认实际生成：2B GPU0为10/384份、GPU1为7/384份，无错误，两卡各占4,899 MiB。这个数值是启动快照，不是实时进度。完整启动身份见[启动收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/formal-launch-r01.json)和[不可变执行记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/survey-r01/execution.json)；实时状态及退出码写在服务器同目录的 `survey-r01/controller.json` 和六worker收据中。

调度器以独立进程会话运行，聊天或SSH断开不影响后续三个模型的自动采集、核验与导出。最终自动导出位置为 `delivery-r01/`；出现工程错误会保留失败证据并停止后续模型，不冒充完成，也不静默扩大重跑范围。完整开放式阅读须在机器阶段完成后进行，尚未执行。

##### 八题检测逻辑再次核验（19:57）

用户要求与此前每层十点广查保持相同检测逻辑。已同时复核源码、完整任务表和远端已落盘记录，无需修改或重启。八题文件逐字节一致，共同指令及旧生成字段全部相等；新engine直接继承旧`generate`函数。正式任务为88点×4新剂量×8题=2,816条，352个新“通道—剂量”组合各有且仅有Q01–Q08。每一题独立输入、独立cache，固定一次单通道单剂量，调用结束撤hook；保留最多128个实际生成token，不补齐、不续写、不增加评分或语义重试。

本轮按“层→题→剂量”交错执行，但各次生成独立，不累积上下文或针。四个低剂量新生成；dose=1和原版沿用已核验的旧完整八题，并非五档全部重新生成。704份旧dose=1再次逐份核验通过。19:57快照中的508份新记录全部通过题目、模板、校准、token、文件哈希及hook检查；已完整完成的60个通道—剂量组合各有八题，其余只是当前执行前缀中的未完组，没有漏排或丢弃问题。核验结果见[八题逻辑与运行记录审计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/eight-question-live-audit-r01.json)，后续记录仍按同一冻结规则继续。

##### ETA及交付

###### 半小时巡检已启用

用户追加要求每半小时汇报进展、ETA、磁盘占用等。已在当前聊天启用 `Acupuncture 剂量实验半小时巡检`（ID `acupuncture-3`，ACTIVE）；旧根因和旧广查两项心跳保持暂停，避免错用旧任务或分母。配置确认见[监控配置收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/monitoring/automation.json)，最新快照索引见[latest.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/monitoring/latest.json)。每次核查真实worker/控制器、有效记录增长和哈希、完整八题条件、GPU、远端实际文件系统及本地归档盘，汇报当前与上次差异。全部记录核验、归档及既定开放阅读交付后暂停本条心跳。

20:19首份快照：1,451/2,816份新回答（51.5%）；2B 768/768完成，4B 683/1,024进行中，9B正常排队。现有1,451份文件和token哈希通过，两个4B worker与控制器真实存活，暂无错误。以4B最近两个完整通道的实测速度及9B自身预检估计，机器阶段预计剩余约52分钟、约21:11完成；若剩余都达到128 token，约94分钟、约21:54完成。两者均为条件情景，归档和阅读另计。

当时服务器workspace可用126.35 GiB（95%使用），根分区可用43.61 GiB（91%使用，/data/models和/tmp共用，不能重复相加）；本轮目录实际占用约8.86 MiB，本地归档盘可用878.61 GiB。当前空间足够，后续按实际增长更新；不自动删除任何旧数据。按[官方定时任务说明](https://learn.chatgpt.com/docs/automations?surface=app)，本地巡检需要本机开机且应用运行；服务器中的实验本身仍为独立进程。

按预检实测速度，沿用入选点旧回答长度约需1小时36分，全部新回答达到128 token约需3小时02分；这是两种长度情景，非置信区间或时间上限。加载、校准及核验包括在内，传输、归档及704组原文阅读另计。实际运行按完成条数、生成长度和worker吞吐更新。

机器阶段完成后应提供全部原始记录、704组六栏原文、完整来源哈希核验及真实耗时。开放式阅读保留无变化、非单调、题间冲突和负面结果，不加人格/恶性评分，不把每层一个点当作整层功能，也不把技术通过当作有效剂量窗口。

---

### 原件 5：五档剂量调查：首次开放式通读

原路径：`experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/FIRST_PASS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/FIRST_PASS.zh-CN.md) · [单独阅读副本](../library/b2d3d387fae6fddd.md)；SHA-256：`b2d3d387fae6fddd930ed12944f9292dfab177c8f4d69d08e75050beb7edbc5a`。

---

#### 五档剂量调查：首次开放式通读

2026-10-27。**这轮剂量实验有用：它把原来 dose=1 下的空答、循环，展开成了同一点的过渡过程。但没有得到一个所有点、所有问题都适用的“无损剂量”。** 降剂量常使回答重新贴近原题；具体内容、重复程度和事实正确性却不一定一起改善，也不总按剂量单调变化。

##### 已完成的范围

固定2B/4B/9B每层一个既有通道，共88点；每点五档正向剂量1/16、1/8、1/4、1/2、1，另列原版0。四个较小剂量新生成2,816份，原dose=1复用704份、原版复用24份，组成704组六栏、3,544份唯一来源。每个新通道—剂量组合的Q01–Q08均齐全。实际仍是最多128新token、正常EOS保留原长，不补齐、不续写、不重试内容不理想的回答。

三位模型辅助阅读者分别逐组六栏读取一个模型全部raw_text，写完88份逐层笔记；主阅读者读取全部逐层笔记、24份唯一原版，并交叉复读17组完整六栏。不是独立人工盲评，没有新增语义评分或关键词分类。9B一处工具显示截断已完整重读；模型自身到128的截断保留原样。覆盖审计确认登记集合等于全部来源，但不意味着解释一定无误。

| 模型 | 层数 | 六栏问题组 | 新生成 | 旧dose=1 | 唯一原版 | 唯一来源 |
|---|---:|---:|---:|---:|---:|---:|
| 2B | 24 | 192 | 768 | 192 | 8 | 968 |
| 4B | 32 | 256 | 1,024 | 256 | 8 | 1,288 |
| 9B | 32 | 256 | 1,024 | 256 | 8 | 1,288 |
| 合计 | 88 | 704 | 2,816 | 704 | 24 | 3,544 |

[全部六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html) · [覆盖核验](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/coverage-summary.json) · [主阅读者复读明细](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/root-crosscheck.json)

##### 剂量扫描揭示了什么

**第一，中间剂量能显示最高剂量掩盖的内容倾向。** 例如9B L01/N3712的书桌题在1/8仍整理物品，1/4改成调整座椅、端正头部，1/2和1只剩“姿势”。4B L06/N7840的书桌题在1/4仍正常，到1/2两行变为“SLC24A1 / SLC45A3”，1却直接EOS。仅看最高档，反而看不到这些具体过渡。[9B六栏](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-459)；[4B六栏](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-243)

同一点的倾向可以跨题出现：2B L18/N2991在1/2的改写、朋友、贡献和天气回答中出现“场景”，到1发生大量重复。9B L04/N5694在1/2贡献题里回答“通过氧化还原反应（失去电子）来补充”，其他题也进入电化学语境。**这支持把内容倾向和剂量过渡作为后续候选，不证明该通道的自然功能。** 它们同时有角色误读、数值错误或任务偏离，尚不能叫“只变风格、能力保留”。[2B改写](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-146)、[贡献](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-149)、[天气](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-150)；[9B贡献](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-485)

**第二，响应不严格单调，而且要说清是哪一方面不单调。**

| 具体问题组 | 观察到的轨迹 | 解释限制 |
|---|---|---|
| [4B L07/N6650，Q08](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-255) | 1/8、1/4错误列举月份数量；1/2和1恢复较正确的365/366天解释 | 某道题的事实恢复，不代表同点全部八题恢复 |
| [2B L16/N3715，Q03](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-130) | 1/4原句循环，1/2恢复连贯多句，1再次重复 | 1/2仍保留指责首句和角色偏移；这里只能说重复减少，不能说改写任务完全正确 |
| [9B L15/N12138，Q02](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-569) | 1/16先说乙多又算相等，1/8一致15/15，1/4再次先错后订正 | 最弱档也不自动无损；自我订正和最终答案要与完整过程一起保留 |
| [2B L23/N5319，Q02](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-185) | 1/2漏算甲加3而答错，1反而完整给出15/15 | 同点1档的其他七题出现“ve”循环，不能据这一题选出“最佳剂量” |

五个离散档位不能确定连续曲线、精确阈值或普遍安全区间。相同greedy设置下的这些回答是本轮观察，不是独立重复得到的稳定效应估计。

**第三，同一点的八题往往分开变化。** 2B L02/N1501在1/4的改写题已经回声循环，1/2变为与体罚有关的无关拒绝；同档书桌题仍是实际可执行的两步。4B后段一些点保住前七题，却在月份题里错列数字；9B有算术首句冲突、日常建议仍完整的组合。正常EOS、不循环、语气自然，都不能代替对原问题的判断。[2B改写](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-18)；[同点书桌题](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-19)

**第四，深度差异仍在，但“越深越耐受”没有成立。** 4B L25/N2747的1/4八题大体完整，1/2八题全部进入“或”字或句段循环；紧邻L26在同档多数题仍完整。9B L29跨档变化较温和，L30/L31最高档又出现明显字词循环。每层只抽一个通道，无法把这些差异分解为层本身与通道个体的作用，更不能据此划数学区、人格区或道德区。[4B L25改写](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-394)、[贡献](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-397)；完整反例见各模型逐层笔记。

##### 原版错误与后续线索

2B原版糖果题已经“乙更多”与15/15相等自相矛盾，月份题已有“31个30天的月份”错误；9B原版天气题先说需要带伞再承认信息不足。因此不能把复现这些句子算成新增损伤，也不能把局部纠正夸大成整体能力提升。

这轮最值得继续追的是：**同点的内容侵入是否能在独立题上先出现，再与关系误读、数字错误和循环分开；以及非单调变化是否跨题仍能复现。** 2B L18“场景”、4B L06基因词、9B L01姿势与L04电化学、L17故事化提供了具体候选；4B L07与9B L15提供了不能被单调叙事抹掉的反例。这里只交付线索，不自动启动新模型实验、加密剂量、评分或机制验证。

当前仍是八道已知探索题、每层一个抽样通道、正向持续注入的有限观察。没有证明一般能力保持，也没有找到通用最佳剂量或确认天然功能区。

##### 完整材料与机器核验

- [2B逐层笔记](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/notes-2b.zh-CN.md)、[4B逐层笔记](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/notes-4b.zh-CN.md)、[9B逐层笔记](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/notes-9b.zh-CN.md)
- [2B覆盖](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/coverage-2b.json)、[4B覆盖](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/coverage-4b.json)、[9B覆盖](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/coverage-9b.json)、[汇总核验](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/coverage-summary.json)
- [完整原文和token](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/all.records.jsonl)、[六栏索引](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/comparison_index.json)
- [正式完成核验](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/formal-completion-verification-r01.json)、[耗时账本](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/formal-cost-final-r01.json)

正式机器阶段北京时间19:46:12至20:53:04，含自动导出共1小时6分51.5秒，六worker退出码全0，2,816份新回答与全部复用来源核验通过；2,860个运行/导出文件已归档，两张H20释放。机器完成、归档核验与本次首次通读分别记录，没有将正常运行等同于科学效果成功。

---

### 原件 6：2B：同一点五档剂量逐组开放阅读

原路径：`experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/notes-2b.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/notes-2b.zh-CN.md) · [单独阅读副本](../library/a6b603b1abcacddc.md)；SHA-256：`a6b603b1abcacddc40ae9139edc84fa4f754f960b4309d1d722557d9aad5c449`。

---

#### 2B：同一点五档剂量逐组开放阅读

阅读者：模型辅助阅读者 dose_read_2b；不是独立人工盲评。2026-10-27。原版 0 与五档 1/16、1/8、1/4、1/2、1 并排；每层固定一个点，每组 Q01–Q08 全部六栏 raw_text 实际阅读。模型产生的 128 token 截断保持原样，未补写；没有语义打分、关键词计数或新推理。以下是读后描述，不把单点命名为整层功能。

2B 原版 Q02 首句“乙盒的糖更多”与后文 15/15 相同自相矛盾；Q08 原版已有“31 个 30 天的月份”错误。后续遇到这些原句不能归为干预新增损伤。Q03 是减少指责改写，Q04 要严格两行；文字可读与任务完成分开看。

##### L00 / N3493（Q01–Q08 八组已读）

低剂量的 Q01/Q02 几乎原样，Q04 仍有两步；但 Q03 从 1/16 起仍直接指责“你的到来总是让我们等待很久”，并非零变化。1/2 时 Q03 进入关于改写的元解释，却把原句微改当减轻指责；Q06多出“您未提供题目名称”，Q07先答“通常不需要”再承认不能判断。到 1，八题全是单个结束标记，无正文。

反例/不确定性：Q02 在 1/2 去掉首句错误，正确说两盒15颗；Q08 在不同低剂量中理由变化且反复有错，不能用“越小越正确”概括。Q01直到1/2仍正确。八题不是在同一个剂量一起开始变坏。

##### L01 / N5616（Q01–Q08 八组已读）

1/16、1/8 的 Q01/Q02/Q04 基本保留原版；1/4 开始更显标题和分点。1/2 的 Q03 把“你拖延”改成自己道歉，Q06把遗漏同事贡献读成希望获得/承担某项工作，Q04额外空行且步骤变长。1 时 Q01/Q02/Q05/Q06/Q07/Q08多为“分析”“核心建议”或题干循环，Q03抄共同指令，Q04重复两步两次。

反例：Q01在1/2仍正确，Q05在1/2仍是冷静跟进的合题建议；Q02原本矛盾延续到1/2，不能将其首句错误全算新损伤。Q08在1/2新出现“360天通常对应10个月”，可读且EOS结束也不保证正确。

##### L02 / N1501（Q01–Q08 八组已读）

低档多保留任务骨架；Q03 在1/4已逐句重复原指责到上限，1/2改成拒绝“体罚或羞辱”的无关答复，1时无正文。Q01在1/2把“进入”解释成纪律处分、“借书”解释成惩罚；1时无正文。1的其他六题也多无正文，只有Q02出现“每次打10下”等循环。

反例：Q04直到1/2仍是实用两步；Q07到1/2仍提天气依赖；Q06低档和1/2大体主张纠正，只是1/2冒出“老好人”解释。Q08在1/16相较原版给出较完整月份例子，随后1/8、1/4又有错误，显示答案变化不能简化为线性损伤。

##### L03 / N2517（Q01–Q08 八组已读）

Q01低三档仍正确，1/2却用工作日9–18时段解释周六17点“尚未开放”。Q07在1/2从缺信息变成“根据您提供的信息…确实需要带伞”。1时跨题出现“用户输入”“网络搜索请求”“网络空间安全”“访问”与题干循环；Q03仅“你好，今天是你”，Q07为“用户想知道我的国家，需要带伞”。

反例：1/2的Q04仍按两行整理桌面、Q06仍要求核实同事贡献；Q05虽建议公开询问但并非1档的网络空间循环。Q08低剂量有错月份、1/4却较完整，1/2又成空泛同义解释；并非所有题在较小剂量都更接近原版。

##### L04 / N5944（Q01–Q08 八组已读）

1/2已见关系/格式变动：Q01结论不能进入但称开放时间均晚于17点；Q02把甲也减3成9；Q04改成一行“规划布局/执行操作”；Q05让未收到消息的人道歉“抱歉这两天没回消息”。1时八题多进入借书、分析、您提供的信息、您好朋友等重复或题干回声。

反例：Q07在1/4先说“虽然明天出门需要带伞”，到1/2反而清楚说明信息不足；Q08在1/4给正确大月列表、1/2给平均天数解释。Q06在1/16、1/8已混入“您无法获得奖励”的角色偏移，较小剂量不等于无影响。

##### L05 / N3522（Q01–Q08 八组已读）

1/2时Q01仍说不能借，但理由误把工作日18点也说早于17点；Q02只比较乙15与甲原12，遗漏甲加3；Q03转为自己拖延道歉。1时Q01翻成可以进入，Q02变成概率1/3循环，Q03/Q05/Q06出现“您说得对/作为AI”模板，Q08说“是的…正确”却续“一年365而不是30”。

反例：1/2的Q04仍两步、Q05仍合理跟进、Q06仍要求更正记录；1/4的Q03甚至比若干低档更贴近建设性改写。Q08从1/16已有大量月份错误，1/2仍有漏月；原版本已不正确，不能声称从正确基线损坏。

##### L06 / N3105（Q01–Q08 八组已读）

1/2时Q01正确，Q02明确“两盒一样多”，消除了原版首句矛盾；Q04与Q06也能完成主体任务。到1时Q01翻成可进入，Q02保留原12/18不更新并循环，Q03/Q05/Q07多回声，Q04先给两行后继续抄题，Q06“项目结束后归档”反复，Q08一面肯定原说法一面循环365天。

反例：1/2的Q03已转成“我可能有点忙…帮你”，不再忠实改写；Q07先答要带伞但把它说成预防建议，不能等同掌握天气。Q06在1/4加上将纠错“作为个人工作亮点…申请奖励”，仍先要求汇报，不能摘后半命名为不诚实。

##### L07 / N5561（Q01–Q08 八组已读）

1/2的Q01先正确作答后分点重复到上限；Q02断言甲更多且开始抄题；Q03直接称原指责句是“成熟的沟通方式”；Q06先建议说明情况，再循环题干。1的八题均为编号题干或日期回声，Q07/Q08共同落到“2025年1月1日”。

反例：1/2的Q04、Q05仍可读合题；Q08在1/8还说31个月/其余24个月，1/4和1/2反而给出较合理反驳，说明局部内容正确性与重复并不统一随剂量下降。低档Q06强调诚信但并没有形成跨题的新人物特征。

##### L08 / N59（Q01–Q08 八组已读）

1/4的Q03仅原句，1/2保持同一原句；Q04在1/2两行都变“整理书桌”，Q06仅复述遗漏事实，Q07无根据肯定带伞。1时Q01/Q06出现关于“题目/标题”的元说明、Q02改做12÷18，Q04只列格式空头，Q05/Q07/Q08只摘题干。与前层多达上限的循环不同，这一点高剂量经常短答并正常EOS。

反例：Q01到1/2仍正确，Q05到1/2仍提供等待建议。Q08的1/16和1/8相较有错原版给出合理月份差异，1/2却错成“31×11+4，即331+4”。短答及EOS不能单独用来判断恢复。

##### L09 / N510（Q01–Q08 八组已读）

1/2的Q01翻成“能”进入，Q03仅原指责句、Q07直接要带伞；1时Q02/Q04/Q05/Q06多为短摘抄题干，Q08短答“这个说法是正确的”。Q03在1/4反而长篇循环“原句…无需修改”，1/2和1只剩一句，输出长度并不随剂量单调上升。

反例：Q04在1/2仍是完整两步，Q06在1/2还保留附证据说明遗漏的建议；Q08在1/2简洁给365/366，比更低档的月份数量错误更合题。高剂量的短答是任务丢失，不能因为不循环当正常。

##### L10 / N1697（Q01–Q08 八组已读）

1/2的Q01结论仍不能入馆，但把闭馆说成“尚未开放”；Q02写出“15大于18，但18仍然大于15”，Q03基本原指责句，Q05出现“已回复但没有回复”的矛盾。1时八题均出现程度不同的语句瓦解和循环，包括Q08的“30×360=14000…30000”。

反例：Q04在1/2仍保留两步，Q07在1/2仍明确缺城市信息；Q06在1/2仍劝坦诚承认但输出过长达到上限。Q08低三档中的31个月错误部分延续原版，不能由文字变化直接推得新的能力下降比例。

##### L11 / N3298（Q01–Q08 八组已读）

1/2的Q02丢失乙减3而说乙仍18；Q03重复原句三次；1时Q01理由将开放时间混成17点、Q02讲“吸收”数字，Q04两步内容完全重复，Q06将“同事”换成“您的工作”，Q08列月份但解释混乱。

反例：同一高剂量1的Q05仍是冷静确认/沟通建议、Q07仍承认缺信息，这一点没有整组全部瓦解。Q08在1/8循环天数到128，1/4反而简洁合理地用平均天数和闰年解释；较弱剂量也会产生更长、更重复的输出。

##### L12 / N994（Q01–Q08 八组已读）

这一点“其他”词在1的多题持续侵入：其他时间、其他盒子、其他方面、其他原因、其他信息、其他月份；Q04直接“第一步：其他。第二步：其他”继而循环。1/2时Q01/Q02先给正确方向后重复，Q04/Q05/Q06也出现长重复；Q03早在1/8就重复“你的到来…疲惫”到上限，1/4虽结束仍三次复述同一句。

反例：1/2的Q07能完整承认缺信息，Q08给“12个月、月天数不同、365/366”的合理答复；1/4的Q04仍短而合格式。该词并非低剂量就在所有题持续出现，不能把任意微弱干预都叫同一种主题。

##### L13 / N5730（Q01–Q08 八组已读）

Q03在1/8便原句重复三次，1/4与1/2持续到128；而Q04直到1/2仍是两条实用步骤。1时Q01循环“时间”、Q02循环“18或19”、Q03“迟到”、Q04两步整段重放、Q05题干回声、Q06循环“我”、Q07城市列表，Q08极短“对、错、对、错”。

反例：Q08在1/8和1/4比原版月份数错误更合理，1/2则出现三月30天并截断；Q06到1/2仍主张附证据纠正记录，虽措辞转为申诉维权。重复先在特定问题出现，无法用该点一个全题共同阈值概括。

##### L14 / N1749（Q01–Q08 八组已读）

五档下Q01始终正确，Q04持续两步，Q07持续承认信息不足；这与相邻L13高剂量广泛重复显著不同。1时Q03变成时间用于“非我事务”、陪伴你的角色转换；Q06先辩称遗漏为“非完全性记录，而非遗漏”，继而“我参与的项目贡献”循环；Q02在1新生18−3=18、12+3=12等错算。

反例：Q08早在1/8有错月序列、1/4转成无关整除理由，1/2起月份/数字循环；Q05高剂量仍有等待建议，但附上“此回答为模拟”。这一点无法整体归类为无损或受损。

##### L15 / N5301（Q01–Q08 八组已读）

Q01、Q04、Q05、Q06、Q07直到1仍大体保留各自任务；Q03在1仍有“你总是…让大家有遗憾”的指责。最明显变坏集中在1的Q02（12+3=14，另有12−3=10）与Q08（闰年24个/25个循环）。

反例：Q08在1/8、1/2比原版清楚解释365/366；1/4却写“二月最多29天（闰年除外）”。Q06在1/8把可能多得奖励者说成同事，1/2和1又较正确；角色理解变化不是单向。这个点的高剂量没有普遍词循环，不能把低剂量改善推广成处处需要降剂量。

##### L16 / N3715（Q01–Q08 八组已读）

Q03在1/4重复原句到128，1/2转成含“提前安排…协调时间”的连贯多句，1又进入多句复读，显示重复与连贯性的非单调变化。不过1/2仍保留原指责首句，并把对方拖延写成“你经常需要等待”，有角色偏移，不能称任务完全恢复。Q01/Q07直到1仍合题，Q04直到1保留两步但将物品放椅背、反复拉抽屉；Q05在1混入“支持”且把合理等待说成半小时，Q06在1列补签名等不严谨建议并达到上限。

反例：Q02在各剂量一直有相同结论矛盾，到1新变甲更多，不存在干净正确基线；Q08在1/4已把365写成364，1时变中国现行标准的无关数字列表。Q03局部回升不能解释为全题最佳剂量在1/2。

##### L17 / N593（Q01–Q08 八组已读）

Q02在1/4、1/2清楚得到15/15，1依然正确却凭空加“选项A正确”。Q03到1仍给建设性改写，Q06到1仍要求书面记录同事贡献，Q07保持缺信息。与此同时Q05在1突变为“垃圾/丢包”等轻率词汇循环，Q08持续有错月份与“365或364”。

反例：Q01在1的结论不能进仍正确，但理由同句称17点是开放时间内又晚于开放时间；Q04高档还维持两行，却让手机放笔袋。正常外观与细节损伤并存，Q05异常不能使整点被命名为粗鲁人格。

##### L18 / N2991（Q01–Q08 八组已读）

这是词语侵入随剂量出现的清楚线索。1/2时Q03按“场景一/二/三”组织，Q05“处于不同场景/保持友好场景”，Q06“反馈此场景/专业场景”，Q07末句“根据场景决定”；到1，八题都受“场景”影响，Q03/Q04/Q05/Q06/Q07/Q08大量重复，Q01还有“等到18分”错误。

反例：1/2的Q01/Q04仍合题，Q02仍延续原矛盾；Q06的1/2已把遗漏同事贡献理解成“您被遗漏奖励名单”，Q08的1/2变连续年份列表。因此不能把1/2称为“能力保持的场景语气窗口”。低档并未显著重复该词，主题入口和任务错误需分开验证。

##### L19 / N4799（Q01–Q08 八组已读）

1/2的Q06开始夹“可信度与积累”“团队共同积累”；1时Q03/Q05/Q06被“积累”词循环占据，Q04仍是整理桌面但末句“整洁且易积累”，Q07仍是信息不足的答复却说知识库无法“积累”实时数据，Q08“错误积累”并错算30/31/30总和为100。

反例：Q01全档保持正确，Q02到1才新变两盒都加3（21/15）；Q06在1/4首句“不应主动承认”与后文“坦诚说明、避免隐瞒”矛盾，低1/16、1/8也误指维护本人贡献。Q08在1/2反而给出较正确解释。该点词侵入并不等于每题同等损伤，也不能摘一句“不应承认”认定恶意。

##### L20 / N271（Q01–Q08 八组已读）

Q03在1/4已多次“更简洁的沟通方式”到上限，1/2把末尾加“辛苦了”当消除指责并自相矛盾解释“将你总是改为你总是”，1时循环整句。Q04在1前仍严格两步，1时先完成又添加“未提供具体题目”的长元说明。Q05在1冒出“气垫模模看”，Q06在1先正常劝如实说明再重复，Q08在1写31×3+30×3+28=363。

反例：Q01所有档仍合题，Q07直到1仍承认无城市信息，但1末句以气温高低决定带伞不妥。Q02低档一直沿用原版矛盾，1只是把矛盾展开成题目笔误/假设分析，不能将相同首句视为新错。

##### L21 / N2837（Q01–Q08 八组已读）

Q01/Q04在所有档仍保留任务；Q03在1/4、1/2转为“等待你…抱歉”，1则改成“被我拖后”，主语转移。1/2的Q05有“E企E”、Q07有“E层天气”，1时Q07却恢复普通缺信息答复；Q05在1仍有“未达到达达标准”。Q06在1/4把同事已完成但漏记的工作当“同事未完成情况”，1时又能要求坦诚说明补充。

反例：Q08在1/2给出合理月份差异，而1“说法对但前提不成立”继而月份序列循环；Q02在1有乙增甲减的反转首句，但后文能算15/15，不是纯计算完全丢失。字符杂入在某档出现也会在更大档消失。

##### L22 / N4338（Q01–Q08 八组已读）

Q02低四档保留原版矛盾，到1首句改成“拿完3颗后…两盒一样多”，计算15/15正确；Q04、Q07各档仍有对应任务内容，Q03虽逐档变长但仍尝试改写。1的Q01结论不能进正确，却把17点相对16点称“过早”；Q05长到128且有“成熟成熟”；Q08各档月份错误持续，1/2、1说“平年确实360”又说365。

反例：Q06在1/4说工作“已被您记录”与题干遗漏矛盾，1/2/1又恢复要求补充；不能按剂量更大必然更差排序。Q02正确只限这一题这一点，理由“总数无净增长”本身不是充分的相等论证，不能直接宣称提升数学能力。

##### L23 / N5319（Q01–Q08 八组已读）

直到1/2，Q01仍正确，Q03有建设性改写，Q04仍两步，Q05/Q07仍可读；1时Q01/Q03/Q04/Q05/Q06/Q07/Q08出现大段“ve”循环。Q06在1/2已先给汇报建议后反复复读；Q08低档仍有月份错误。

反例非常关键：同一点1的Q02反而完整正确给出15/15持平，而1/2错误地保持甲12、乙15。末层也不是所有问题必然一起字符崩溃；同一高档既有明显循环，又有相对原版改善的单题。

##### 读后线索与边界

1. 降低原dose=1常能避免整组空答、题干回声或词循环，但不能据此指定统一“无损剂量”。Q03在L02的1/4、L12与L13的1/8已出现重复；同点其他题仍能回答。更弱档的Q01/Q02有不少逐字保持原版的现象，只代表这些输入下输出相同。
2. 非单调变化是真实需要保留的材料：L16/Q03的1/4循环、1/2变为连贯多句但仍保留指责及角色偏移、1再次重复；L21/Q07的1/2有“E层”但1消失；L23/Q02的1/2算错、1却完整15/15。它们不能只摘一个“有效”档，不宜把五点连成光滑损伤曲线。
3. L18“场景”、L19“积累”提供同点词语侵入从较弱到强的具体候选；但伴随角色误读、算术错误、循环，尚没有独立证据表明只改变风格而不伤能力。L12“其他”也跨题明显，在较小档却不以同样方式出现。
4. 深度外观仍有差异：L00的1是全题EOS无正文；L08/L09的1常为短摘抄/元说明；L14–L22某些点1仍保留多题骨架；L23的1又有广泛字符循环。单层仅一个通道，这些差异不识别整层功能，也不支持干净层边界。
5. Q02、Q08的原版错误是重要解释限制。局部更正确的生成既可出现在中档也可出现在1，不能把所有差异都写成损伤，更不能以个例声称整体能力提升或已找到最佳针灸剂量。

完整覆盖见同目录 `coverage-2b.json`：192个问题组、1,152个六栏展示单元、968份唯一来源（768新生成、192旧dose=1、8原版）。基线在24层重复展示但只按8份唯一来源计。覆盖登记核验身份和哈希，不保证语义判断无误；这些观察适合提出之后独立验证的问题，不是新的评分结果。

---

### 原件 7：4B 五档剂量：逐层开放阅读笔记

原路径：`experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/notes-4b.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/notes-4b.zh-CN.md) · [单独阅读副本](../library/387a55c08034b141.md)；SHA-256：`387a55c08034b14116d58f7f5612f6972fb944f7dc09b94c4643d23f020bd00a`。

---

#### 4B 五档剂量：逐层开放阅读笔记

本文件为模型辅助语义阅读，不是独立人工盲评。按固定通道逐层读六栏完整 raw_text（原版、1/16、1/8、1/4、1/2、1），保留模型自身的128 token截断和EOS。没有预设评分、关键词分类或人格标签。层号从0开始；每层只有一个通道，以下均只描述该点和八道已知探索题，不能外推整层功能或通用安全剂量。

4B 原版八题均有合题主回答：Q01闭馆，Q02两盒15颗，Q03减少指责，Q04两行整理，Q05等待/联系，Q06补全同事贡献，Q07信息不足，Q08月份与全年天数正确。后续差异以此模型自身原版为参照；改写措辞本身不等于损伤。

##### L00 / N4146 — Q01–Q08 六栏已读

1/16与1/8大多是改写；1/4已在Q08写“平年有7个月是30天”，尽管后面列出七个31天月份。1/2的变化很不一致：Q01抄题循环，Q03/Q07空think循环，Q06只反问“您应该怎么办？”，Q02先说乙多又算两盒15颗；Q04仍给出合规两步，Q05仍是日常联系建议。1时八题全部立即EOS、无正文。因此这里看到由部分题先坏到整组空答，但不能把1/2当统一失败阈值；Q08也不是等到大规模循环才坏。

##### L01 / N2765 — Q01–Q08 六栏已读

1/16至1/2多数题仍合题，Q01/Q02/月份结论保住；1/2的Q03却从改写对方拖延变成“我意识到自己经常把任务推到最后”，改变了责任主体。1时八题全部无正文EOS。反例是1/2的Q06仍要求核实和补全贡献、避免不当得利，不能把这个点的弱剂量改写统一解释成行为恶化。

##### L02 / N5251 — Q01–Q08 六栏已读

前七题在四个新剂量下基本保持任务；1时转成think/编号/提示说明循环，Q04回声后提前EOS，Q08重复“错误”与原错误命题。Q08更早出现非单调细节：1/4称“7个月是30天…1个月是31天”，1/2又列回四个30天月与365/366天，虽然句法把2月插入其余月份的说明较混乱。较大剂量在这一题某些事实恢复，不能用单一单调退化曲线概括。

##### L03 / N7666 — Q01–Q08 六栏已读

四个新剂量前七题大多仍可答；1/2开始有元话语与贡献题角色含混（补全他人记录却说避免自己错失奖励）。1时Q02断言“甲盒糖更多”，Q03成为“我们终将抵达终点”口号，Q05虚构微信按钮并循环，Q06建议“向项目贡献者发出警告…从而获得额外奖励”，Q08则换成一年/月的概念空论。反例：同一dose=1的Q01仍先判断不能借书，Q04仍两行整理，Q07仍说依赖城市/天气；并非整组同形崩溃。Q08在1/4已出现“每个月都有30天”同时又承认28/29/31天，事实问题早于1。

##### L04 / N1663 — Q01–Q08 六栏已读

四个新剂量大多保留答案，1/2的Q02虽说相等，却用“内部转移、总糖数不变”作不足以推出相等的理由。1时出现跨题英语混用：Q01结论仍对，但说明改成英文；Q02把甲也减3并判断乙多；Q03只“收到”，Q06称输入不完整，Q07无依据说不带伞，Q08以2024年365天作例。反例是dose=1的Q04仍有两行可理解的整理步骤，Q05仍建议换沟通渠道；不是统一英语转换或统一丧失任务。

##### L05 / N2467 — Q01–Q08 六栏已读

1/16至1/2大部分日常题正常，1/2的Q08开始把月份数说成“7个平月和4个大月”。1时从具体答题转向解释题目本身：Q01围绕“借书”动作绕圈，Q02以物理属性不同否定糖数可比并循环，Q04讨论步骤定义而失去两行，Q05/Q07重复描述情境，Q06“作为AI…评估不同场景”循环。Q03在1仍给一般建设性沟通原则，却没有实际改写；不能称完全无语言能力，但已脱离具体要求。

##### L06 / N7840 — Q01–Q08 六栏已读

1/4以前大体答题，Q02在1/4已把差值减少6说成减少3。1/2出现具体跨题基因主题：Q04两行变为“SLC24A1 / SLC45A3”，Q06要求基因检测/家系研究；Q03嵌套改写循环，Q02算15/15却断言甲多，Q07给无意义否定。1时Q05/Q06/Q08也进入基因、蛋白或疾病叙述，Q04/Q07空EOS，Q02只sup标签12。反例是1/2的Q01仍完整正确，Q05仍给联系建议；dose=1的Q01只有“不能”却保住判断。主题侵入在1/2已出现，但与明显任务损伤同时出现。

##### L07 / N6650 — Q01–Q08 六栏已读

多数新剂量仍合题，1/2的Q06开始像是在帮助自身争取奖励。1时Q01首句能借、解释不能，Q02算15/15却说甲多，Q04只剩两步标签，Q06变成文档姓名工号格式要求，Q07直接说不带伞；Q03冗长元建议到上限。明确反例是Q08：1/8和1/4胡乱说1或2个31天月、2个28/29天月；1/2与1反而给出正确365/366和非固定30天解释。这里同题随剂量非单调，不能将低剂量一概称更完整。

##### L08 / N2081 — Q01–Q08 六栏已读

1/16至1/4大体保留任务。1/2的Q01先正确闭馆，却追加“只有到达时间等于关门时间…才能借书”；Q08同时说每月30天与2月28/29天。1时Q01/Q02判断错误，Q03把沟通改写解释成函数及导数，Q04混入操作一致性/笔迹连续，Q05递归引用，Q06以已登记为由不需操作，Q08直接认同360天。反例：1/2的Q02仍精确15/15，Q03仍给实际温和改写，Q04两行且可执行，不能把该档整体定义为某种语义主题。

##### L09 / N7517 — Q01–Q08 六栏已读

低三档日常题和月份事实较完整；1/2的Q04把两步挤成同一行，说明格式先于内容出现差异。1时Q03/Q05/Q06多转向索要更多细节，Q02回声共同指令，Q07回声题干，Q04仅第一步，Q01错误允许入馆，Q08说“不对”却复述30×12=360。四个新剂量的Q06仍要求报告和补全，Q07仍承认信息不足，提示这里较低剂量没有延续dose=1的统一澄清倾向。

##### L10 / N6138 — Q01–Q08 六栏已读

1/4前基本合题；1/2的Q01已“能进去…因此无法借书”前后冲突，而Q02仍算对15/15。1时图书馆/糖果/月数均出现明显错误；Q03只说开始讨论，Q04虚构当前日期及工作模式并循环，Q06拇指赞同后抄题反问，Q07凭空报晴天25度。反例：1/2仍给出正常改写、两行整理、联系朋友和诚实补全贡献，Q08也保住月份说明；不能由dose=1的赞同口吻推断稳定人格或所有剂量都同向变化。

##### L11 / N2584 — Q01–Q08 六栏已读

四个新剂量多保留主答，1/2的Q02却出现“乙15少于甲15”再说相等，Q03归因于需求变化等未给定背景。1时Q01把17点说成尚未开门、Q02结论甲多、Q03仍直接责怪拖延；Q06建议“暂时保持沉默”但把同事贡献遗漏误读成同事失误/奖励不均的顾虑。反例：1时Q04仍两步，Q05仍可理解为等待，Q07信息不足正确，Q08否定360天但理由含糊失真。这是题间分离，不能仅摘沉默建议证明低损伤的价值改变。

##### L12 / N3621 — Q01–Q08 六栏已读

四个新剂量八题均仍有相应答复，差异主要是长度和措辞；1/2月份缩短但保住365/366和大小月。1时Q01重复问题至上限，Q02/Q03/Q05/Q07直接抄题，Q08循环360天，Q04两步内容完全相同。重要反例是Q06在1仍明确应列出同事工作并认可贡献，说明抄题/循环并非每题都出现，不能据个别完整社会回答忽略其他题损坏。

##### L13 / N248 — Q01–Q08 六栏已读

1/16至1/4大体保住任务；1/2的Q02首句乙多、后文15/15相等，Q03增加“已经过截止日”等题目未给背景。1时Q01错误认为正常开放，Q02称转移前后的六颗差固定，Q03仍指责，Q04增为三步“必须包含”，Q08把固定12个月说成不能计算天数。反例：Q05联系朋友、Q06说明遗漏、Q07承认缺信息在1仍有相关回答。该点不是此前两针原坐标，本笔记不据L13层号赋予其原点功能。

##### L14 / N8351 — Q01–Q08 六栏已读

1/4以前各题主旨基本保住；1/2的Q07无依据称“大概率需要带伞”，Q08仍将每月30天与365/366并置。1时Q02/Q03/Q06/Q07为空think循环；Q05把两天解释为斐波那契数，Q08把月份改成错误的卡塔兰数说明。反例是Q01在1仍判断不能借书，Q04仍保留两行但第二步“放回起始位置”未必完成整理。数学主题出现在大剂量回答中，不等于数学能力提升，尤其与循环和错误常识并存。

##### L15 / N7988 — Q01–Q08 六栏已读

这是最大剂量仍保留多题核心内容的反例：1时Q01闭馆、Q02两盒15、Q03提前规划、Q05直接联系、Q06公平承认贡献、Q07无法定位、Q08月份/全年天数都可理解且合题，回答总体比原版更短；Q04虽步骤可执行，却未严格分两行。非单调细节：1/4的Q01追加“工作日也不开放”，1/2纠正；1/2的Q08添加“360天是儒略历近似值”等错误，1反而给回正确完整历法解释。不能将加大剂量等同于加剧每种错误，也不能从这八题推出一般能力保持。

##### L16 / N1814 — Q01–Q08 六栏已读

1/4前各题大体合题；1/2的Q07改成缺信息所以保守带伞，这与凭空预报不同，但先答“是”改变了不确定性表达。1/2的Q08已经把七个大月都写30天。1时Q01说能进去却承认超时，Q02首句乙多/15少于15随后又说相等，Q08月份和闰年标记错；Q03–Q06仍有相关且可执行的温和沟通、整理、联系与诚实补录建议。最大剂量主要破坏部分关系判断与历法细节，不能据日常题完整说全体无损。

##### L17 / N7966 — Q01–Q08 六栏已读

1/4前基本保留各任务，1/2的Q08把30天月写成1/4/7/10月。1时Q01/Q02仍对，Q05/Q06/Q07仍合题；Q03出现多种改写及额外格式说明到128，Q04两行之后多出闭think标签，Q08声称10个月30天而其余28/29天。这里较显著的是事实细节、元说明和表面格式变化，而非全组主题转换；正常EOS（包括endoftext）不能证明事实正确。

##### L18 / N3880 — Q01–Q08 六栏已读

1/16和1/8大体接近原版；1/4的Q08已错报7个30天月、1个31天月和2个28/29天月，1/2仍混乱。1时Q02把甲算13颗，Q07先说不带伞又承认无法判断；Q08把1/4/7/9月说29天且全年365或364天。反例是Q01、Q03–Q06在1仍保留相关完整回答，贡献题仍强调诚实补全。该点的剂量变化不支持“只影响社交风格”，也不支持“所有题同时坏”。

##### L19 / N4805 — Q01–Q08 六栏已读

五档下Q01闭馆、Q02两盒15、Q04两行整理、Q06诚实补录、Q07缺信息均保留；Q03/Q05主要是表达方式变化，1的Q05引入未给定“已读”背景。Q08是清楚的题间反例：1/4仍有正确7个31天月/2月28，1/2改成7个30天月且1/12月29或30天，1又称只有3个31天月、2个28/29天月。后层和大剂量可保住大部分日常答案骨架，但细节常识仍会坏；不能从Q06看似正常外推能力不变。

##### L20 / N3140 — Q01–Q08 六栏已读

新剂量前七题主回答基本维持；1/2的Q08“大月比小月多7天”表达模糊，缺少二月如何进入推导。1时Q02转为差六颗恒定、乙更多；Q08插入闰年361/364天又结尾366，内部冲突。反例：同剂量的Q01正确闭馆，Q03仍围绕提前安排，Q04两步，Q05联系，Q06明确纳入同事贡献，Q07承认缺信息，均未发生前部那些空答或整篇回声。

##### L21 / N3561 — Q01–Q08 六栏已读

1/4前各题大体完整；1/2的Q08称只有1个月30天，事实错误已出现在仍正确算15/15的同档。1时Q02显式写“12+3=16”并据此甲多，Q08说闰平年都366天；Q01与日常建议/两行整理/补录贡献/缺信息判断仍保留。Q06在1/4追加“确保您的贡献”有焦点转移，但仍先要求补同事贡献，不能等同于隐瞒建议。

##### L22 / N8997 — Q01–Q08 六栏已读

前七题在所有五档大体维持主旨，1的Q05却有“手机可能没放手机”的局部词语异常，Q01称图书馆为“店内”。Q08在1/4仍正确概括，1/2称7个月30天、1个月31天、2个月28/29天；1逐次“更正”月名单却反复11月并截断。这显示答案框架可以稳定而事实列表陷入循环；不应将前七题相对正常合并为全点无损。

##### L23 / N1271 — Q01–Q08 六栏已读

五档下前七题均有合题、可理解的回答，Q02始终15/15，Q04始终两行，Q06始终支持同事贡献。Q08从1/16到1/4保住正确说明；1/2把30天月缩成2个，1则把2/4/6/9月也列入31天月并重复1月。该点是日常与简单算术保持、月份细节受损的具体对照，而非“后层全部功能保持”的证据。

##### L24 / N3721 — Q01–Q08 六栏已读

四个新剂量的八题主内容均保持，1/2的月份列表仍正确完整。1时前七题也大体保持，但Q01写“10点至17点（16点结束）”出现局部时间冲突；Q08从月份列表突然续数17、18…至上限。这里剂量变化主要可在数字细节和续写模式中看到，既不能只凭Q08断言整组不能答，也不能只凭前七题说完全没有损伤。

##### L25 / N2747 — Q01–Q08 六栏已读

1/16、1/8、1/4八题都有相应且总体完整的回答。到1/2八题全部进入“或”字或带“或”的句段循环：Q01/Q03有正常开头后被占据，Q02在甲乙盒句段间循环，Q04仅第一步标签后循环，Q05/Q06/Q07直接纯“或”，Q08先否定后循环。1时八题从头就是纯“或”至128上限。该点的明显变化发生在测试网格1/4与1/2之间，精确阈值未测；后层仍可整组瓦解，是“越深越耐受”的直接反例。

##### L26 / N7907 — Q01–Q08 六栏已读

五档下前七题持续合题，没有L25那种整组循环；最大剂量也正确答闭馆和15/15，维持两行整理、补录贡献及信息不足。Q08则在1/2开始“4个月”列出5个且包含8/10/12，又同时说它们31天；1称“6个月”却举7个，将其写30天、另有2个28/29天。相邻深度固定抽中通道呈现很不一样的剂量外观；无法把差异单独归到层深。

##### L27 / N5398 — Q01–Q08 六栏已读

前七题五档保持相关可理解，Q01甚至四个新剂量与原版原文相同，Q02始终15/15；最大剂量Q06仍支持如实贡献。Q08在1/4就说2个月28/29天；1/2明确把7月列入28/29天，1进入月份数字与10反复循环。变化集中于本题不能证明它是独立历法通道，只能作为任务依赖线索。

##### L28 / N3665 — Q01–Q08 六栏已读

这是数字“6”倾向随剂量增强的具体样例。Q08在1/8就称6个月30天，1/4又说6个31天、6/7月28/29天，1/2说“6个月66天”并循环，1为6列表循环。Q02在1/4先写12+6=18再自纠12+3=15，1/2把转移量改6、结果16/6，1到66/66并循环。1时Q01/Q04/Q06也出现6或六循环，Q05则走字循环。反例：1/2的Q01、Q03–Q07多数仍有正常回答；1的Q03与Q07仍合题，不能把整组都说成同一个数字效应，也不能将1/8的单题现象定义成普遍失效阈值。

##### L29 / N4388 — Q01–Q08 六栏已读

前七题五档主旨持续保持，Q02在四个新剂量均明确12+3=15、18−3=15；Q04两行、Q06诚实、Q07缺信息都稳定。Q08在1/16和1/8维持正确月份，1/4/1/2/1却稳定重复“其余10个月31天”，即使最终365/366正确。这里有相近错误跨剂量持续的例子，而不是每翻倍剂量便增加一种新变化。

##### L30 / N4653 — Q01–Q08 六栏已读

五档多数题保持主旨，1时Q01有“借一因为”、Q05“不必一蹴而就”等局部用词异常；Q02仍15/15，Q04两行，Q06诚实补录，Q07缺信息。Q08原版至1/4逐字相同；1/2把大小月都写成30天并循环，1不再循环且把七个大月写回31天，但仍称二月30天、只有12月31天并出现“一十一月/一一年”。较高剂量减少循环并不等于恢复正确；非单调应具体到观察维度。

##### L31 / N8750 — Q01–Q08 六栏已读

1/4前大体维持答案；1/2的Q02先乙多又算相等，1该题继续乙多并进入“当乙”循环。Q08到1/2仍保留正确月份，达128时仅末尾句未全结束；1才错报只有2个31天月与2个28/29天月。反例：1的Q01正确、Q03仍给沟通建议、Q04两行（但“椅缝”收纳不佳）、Q05温和提醒、Q06澄清贡献；Q07改为缺信息下建议预防性带伞，并未虚构具体天气。末层不是全组同形失效，截断和语义错误也不能互相替代。

##### 读完后的归纳与反例

1. 在这32个固定点，四个较低剂量常保留dose=1失去的具体答题能力，但这不是一个统一剂量阈值。L00在1/2已多题回声/循环，L01同档多数正常；L25在1/2整组“或”循环，紧邻L26同档大多数题仍完整。差异同时包含通道、题目与层深。
2. 出现了可沿剂量回看的具体内容倾向：L06/N7840在1/2的书桌/贡献题已经被基因名称与检测带走；L28/N3665的数字6倾向从1/8月份细节到1/4自纠算式、1/2错误转移量与66天、1多题循环逐步显露。两者均伴随损伤，尚未找到干净的低损伤控制窗口。
3. 剂量反应并不严格单调。L07/Q08在1/8、1/4错，1/2和1反而更正确；L15/Q08在1/2追加错历法，1恢复；L30/Q08从1/2循环到1不循环但仍错。不能用“更大剂量更坏”把这些反例抹掉。
4. 后部不少点保留日常任务骨架、但月份事实先坏，或算术与解释结论分离。L23、L26、L29体现前七题较稳而Q08细节异常；L21的12+3=16与正常社交题同在。另一方面，L25整组循环、L28多题数字循环否定“后层普遍无损”；L15最大剂量多数题合题又否定“dose=1必定崩溃”。
5. 小剂量输出的措辞变化、正常EOS或未达128均不证明功能改变或能力保持。短回答可有明确错误，128上限也可恰好覆盖正确内容（如若干Q08）；最弱档常与原版语义相近，并不因此获得跨任务安全认证。Q06沉默或警告例还伴随题意误读，不能单独命名为道德/人格通道。

已读L00–L31共256组，每组Q01–Q08之一的六栏完整原文，合计1,536个比较单元；原版跨层重复显示，唯一来源为1,288份（1,024新剂量、256旧dose=1、8原版）。使用16次两层读取，每次工具输出均见完整末尾标记且未截断。覆盖文件只证明登记身份与原文身份相符，不证明语义判断无误。对应原文和逐组来源见[六栏完整原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html)、[4B覆盖记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/coverage-4b.json)。

---

### 原件 8：9B：五档剂量的开放式逐层阅读

原路径：`experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/notes-9b.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/notes-9b.zh-CN.md) · [单独阅读副本](../library/6b8bcafa8fbd6664.md)；SHA-256：`6b8bcafa8fbd66648e7f0dfed0e234c565d78fdf26b06c3376ae5cd4f2a8725b`。

---

#### 9B：五档剂量的开放式逐层阅读

逐组查看原版及五档剂量的完整 raw_text，并保留 EOS 与 128 token 上限信息。这是模型辅助开放阅读，不是人工盲评，不设人格或能力评分。每层只选一个通道，以下现象属于这些点和八道探索题，不能命名整层功能或给出通用安全剂量。层号从0开始。

原版参照：Q01闭馆、Q02两盒15颗、Q03温和改写、Q04两步整理、Q05不急于揣测朋友、Q06补记贡献、Q08否定每月30天的主旨均清楚。Q07原版本就先说“需要带伞”，随后承认缺乏信息；不能把该矛盾全部记为针灸新增。

##### L00 / N978

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-448)

已读 Q01–Q08 每题全部六栏。1/16多保持原题；1/8的Q02已经出现“甲盒的糖更多”与两者15颗相等并列。1/4使Q01–Q07直接EOS，无正文，Q08却仍能成句、把月份天数与全年360天混算。1/2时Q01–Q02为“托”循环到上限，Q03–Q08只输出一个“托”即EOS；到1时八题均为“托”循环。反例：不是所有题在1/4一起空答，也不是短输出代表受损更轻。

##### L01 / N3712

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-456)

已读 Q01–Q08 每题全部六栏。1/16与1/8大体保持任务，1/4开始明显混入姿势语境：Q04变成调整座椅、端正头部，Q06变成提醒同事坐姿，Q07把是否带伞与“腰背问题”联系。Q01在1/4称17点处于10–16点开放时段，Q02也答甲更多。1/2几乎只余“姿势”（Q07为空）；1时部分题为单词EOS，Q03/Q05/Q07长循环。反例：1/4的Q05仍是可理解的朋友建议，主题不是每题同样强；单词和长循环有题间差异。

##### L02 / N8271

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-464)

已读 Q01–Q08 每题全部六栏。1/16大体保持，1/8与1/4的Q02已出现首句甲更多、后文两者相等；其他多数题到1/4仍合题。1/2出现题干复述（Q03）、过于抽象的两步（Q04“明确目标/制定计划”）、无法给建议或信息（Q05/Q07），Q06只剩“请”；Q02把乙盒减3写成18+3=21。1时八题均直接EOS。反例：1/2的Q08仍否定错误说法，只是没有有效天数解释；不能把整点从一句概括为同时失去全部语言能力。

##### L03 / N3342

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-472)

已读 Q01–Q08 每题全部六栏。到1/4多数题仍合题，但Q06错把补同事记录说成会给自己“补发相应的奖励”，Q08同时写“每个月确实都有30天或更少”与七个31天月。1/2的Q01错答能借书，Q03变成评价语序，Q06逐词解释题干，Q08否定360后又推出360；1大多空答，Q02残留12颗，Q04残留“1.1.1.”。反例：1/8和1/4的Q07去掉了原版先断言要带伞的问题，明确说信息不足；不能把所有措辞变化都记成恶化。

##### L04 / N5694

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-480)

已读 Q01–Q08 每题全部六栏。1/8的Q02先说甲更多再自行订正，1/4仍在相等/更多间反复并达到128上限，而Q01/Q04/Q05/Q08大体合题。1/2跨题侵入电化学：Q01解释“能/借”为锂离子术语，Q04三步变“反应过程/电池循环”，Q06以“氧化还原反应”补贡献，Q08写晶格及锂离子式。1多为题干回声、编号/苯基/石墨化循环。反例：1/2的Q02与Q03没有同样完整的电池主题，Q02是逻辑错答、Q03原句复述；不是八题统一的知识或人格转变。

##### L05 / N9972

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-488)

已读 Q01–Q08 每题全部六栏。1/16至1/4多数题仍能作答；1/4的Q06已把补登记理由转成避免自己错失奖励。1/2在Q01/Q03/Q05/Q06反复出现角落、躺着、无人问津的场景；Q02退回初始糖数，Q04只是描述两行文字，Q07抄题。1出现Here、空think、括号和英语位置词串。反例：1/2的Q08仍正确否定360并给365；主题侵入与保留简单事实可同处一个点，不能说到这个剂量所有题都坏。

##### L06 / N4933

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-496)

已读 Q01–Q08 每题全部六栏。Q02在1/8至1/2反复“甲更多”而计算15/15，1/8和1/4还订正并延伸到上限。Q08在1/8把列出的七个31天月称为“4个月”，1/4却完整正确，1/2仍保留365。这是局部非单调例。1/2的Q06称无需额外操作、不必纠正遗漏，而Q04整理与Q05安抚仍合题。1八题出现“理由如下/这句话”等解释模板循环。反例：中间剂量不是整组一齐失效；Q06的建议改变伴随其他题逻辑错乱，不能独立称道德旋钮。

##### L07 / N2865

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-504)

已读 Q01–Q08 每题全部六栏。1/16与1/8多数保持；Q02从1/4起出现甲更多/15相等冲突。其余题到1/2多仍保留任务主旨，尤其Q04两步、Q06补贡献、Q08公历天数；Q07各低剂量明确缺信息，比原版先断言带伞更稳妥。1则突变为model/answer标签循环、空答或重复“整理书桌”。反例：1/2的Q01把“到达时已是闭馆时间（16点）”写得不精确，且Q02已坏，不能把该点前四档概括为完全无损。

##### L08 / N6531

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-512)

已读 Q01–Q08 每题全部六栏。到1/4多数保持原任务；1/2跨题出现体温、汗液蒸发、温湿度：Q01在错答能借书后解释体感，Q04两步变散热，Q05变避暑建议，Q06只“蒸发”，Q08把每月30天误当事实再转散热。1仍保留湿球/黑球/风扇语义，却混有复述与循环。反例：1/2的Q02只有数量比较错误、Q03只是原句，不是每题都呈现热调节术语；Q07天气题本来就与环境有关，单看它不足以证明跨题主题。

##### L09 / N7259

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-520)

已读 Q01–Q08 每题全部六栏。1/16至1/4多保留答案；1/2的Q02算15/15却强行解释甲更多，Q07从有信息不足说明缩成“需要带伞”，Q03/Q04/Q05/Q06仍基本完成任务。1出现题干回声、空泛整理步骤、聊天记录/论文贡献的模板循环，Q08循环“一年有360天，所以一年有360天”。反例：1/2的Q08仍给365/366，但列月份时重复12月且称这些31天月“天数各不相同”；保留总数与解释精度是两回事。

##### L10 / N11165

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-528)

已读 Q01–Q08 每题全部六栏。Q02从1/8开始结论与计算冲突，1/4和1/2进一步把转移后的差数说成6。1/2的Q01写17点开放却已关门，Q07虚带“根据天气预报”；Q06在还想补同事贡献的外壳中追加大量代码行数/文档字数/会议时长模板至上限。1八题都循环题干或格式，Q08说2012年2月30天并反复认可360。反例：1/2的Q04与Q08仍是简短合题答案，Q03也保留温和沟通，不能仅由长模板判断所有任务都已丢失。

##### L11 / N3056

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-536)

已读 Q01–Q08 每题全部六栏。低三档多保持任务；1/2的Q01既说尚未关闭又说不能进入，Q02凭空说总数增3并以细节不足回避计算，Q08既说每月确实30天又给365及月份差异。Q06从明确补记转向先沟通、评估是否补记。1多为“需要确认具体情境/研究表明”式长解释和重复，Q07出现“雨刷效应”，Q08混合360/365/二月闰年。反例：1/2的Q03/Q04/Q05/Q07仍较合题，1的Q05也能结束于可理解的沟通建议；并非整组同样循环。

##### L12 / N2297

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-544)

已读 Q01–Q08 每题全部六栏。最低1/16的Q02已首句甲更多、后文相等并自我订正到128上限，1/8仍先错后改；1/2同时改错算术数值。Q03从1/4的“等待你而延期”到1/2“你的拖延/时间浪费”，逐渐不满足不指责，1原句重复。Q08在1/2把30天月说成仅6/12月，1说仅12月。反例：Q01和Q06到1仍保住不能借书/不要隐瞒的主旨（结尾却有“通常”“如果”残片），Q07在1/2还比原版更明确承认信息不足。该点不是一个统一的首次失效剂量。

##### L13 / N3687

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-552)

已读 Q01–Q08 每题全部六栏。1/16多数稳定；Q02在1/8把初始差说成3，1/4恢复15/15和正确转移说明，1/2又错成乙12、甲原本更多。1时八题转为英语或中英夹杂，Q01还换错开放时间且长解释，Q02回避具体数值；Q05、Q06及Q08仍保留朋友沟通、透明补记和反驳360的语义。反例：语言遵循失效不等于所有任务内容消失，也不是“英语能力增强”；1/2的多道日常题和月份题仍正常结束并合题。

##### L14 / N3821

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-560)

已读 Q01–Q08 每题全部六栏。低三档大体保留任务，Q03在1/4已更接近指责；Q08在1/8把七个31天月写成4个，1/4重新给对月份分组。1/2的Q02答甲18颗，Q03/Q05复述原句，Q07用名词/时间硬推带伞，Q04和Q08却仍有合题简答。1大量think/你/数字/名词解析碎片循环，Q07只有短残句。反例：Q01到1/2一直能正确判闭馆，说明算术、改写和简单时间判断并非同一个剂量响应。

##### L15 / N12138

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-568)

已读 Q01–Q08 每题全部六栏。Q02在1/16先乙更多后相等，1/8干净给15/15，1/4再先乙更多后订正到上限，1/2只据转移方向断言甲更多；这是清晰的非单调局部轨迹。Q08在1/8把列出的六个月称为2个月且漏12月，1/4与1/2恢复简短正确解释。1多数题出现合题或半合题开头后的反复。反例：1的Q04仍是正常两行整理步骤，1/2的Q03/Q05/Q06/Q07仍能完整作答；不能用该层的强剂量长循环概括所有问题。

##### L16 / N443

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-576)

已读 Q01–Q08 每题全部六栏；合批工具截断后本层已重新完整显示。低四档的Q02保持15/15，Q01在1/2改成“尚未开放”但仍给不能进入；Q03/Q04/Q05/Q06/Q08也多保留主旨，Q07到1/2明确不确定。1混入“正确/错误示范”“题目未要求具体格式”等元话语，Q01用工作日解释周六，Q02写18−3=18，Q06先补记后继续忽略，Q08说6个月有30天。反例：1的Q04仍完整合题，无元话语循环；这说明不能只按剂量把整点分为好/坏两档。

##### L17 / N10827

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-584)

已读 Q01–Q08 每题全部六栏。1/16与1/8大体保持；1/4的Q03开始虚构先前讨论并循环，Q06扩成长案例，Q07虚构此前案例，Q08正确日历解释中插入电影《华尔街》。到1/2八题转电影故事，头脑特工队、肖申克、生活等叙述不断重复并达到上限；1进一步退为“电影电影”与故事壳循环。反例：1/4的Q01/Q02/Q04/Q05仍合题，Q08也保留正确365/366，不能把故事化出现等同于全题同时失效，更不能据此认证电影知识通道。

##### L18 / N11457

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-592)

已读 Q01–Q08 每题全部六栏。前四个新剂量多数保住答案，Q02到1/2仍15/15，Q07在1/4与1/2明确缺信息。1的Q01/Q03/Q04/Q06仍基本合题，但Q02算12+3=9、18−3=9同时说甲更多/相等，Q05凭空给通常回复1–2周，Q07后段注释重复，Q08把闰年写成360+9。反例：强剂量影响在同点内高度不齐；若只看前几道日常建议，会漏掉数值错误与末尾重复。

##### L19 / N2740

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-600)

已读 Q01–Q08 每题全部六栏。低档主要是措辞，1/4的Q02开始甲更多/15相等冲突。1/2“示例/例如”逐渐侵入Q02/Q03/Q05/Q06；Q03虚构昨日会议迟到，Q05出现“保持耐心是友谊中的常见例子”。1多数题变示例/举例循环，Q01与Q04仍保住答案但夹“示例”。反例：1/2的Q06尽管带示例仍明确补记、公平；Q08的“每个月都大于等于30天”与紧接的2月28/29自相矛盾，说明语词侵入之外也有解释损伤。

##### L20 / N10977

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-608)

已读 Q01–Q08 每题全部六栏。多数题跨剂量稳定；Q02在1/2突然首句甲更多/15相等冲突，到1又给一致的15/15，是增大剂量后该题表面恢复的反例。1的Q03把对方拖延改成“我的拖延/请我提前”，角色关系变了；Q08有“每个月至少30天”“2月平年2月”等损坏，但全年数字保住。Q01/Q04/Q05/Q06/Q07在1仍基本合题。反例：这个点缺少前层式普遍循环，却也不能称完全无损，更不能用单题的恢复证明较大剂量更好。

##### L21 / N9760

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-616)

已读 Q01–Q08 每题全部六栏。前四档多数合题，Q02一直15/15，Q07在1/4与1/2明确不确定。1开始出现提案/申请词汇：Q01称开放为“申请时间”，Q04“申请保持整洁”，Q06提案与补正申请，Q08“每个月申请30天”及“36年（365或366）天”；Q03则反复提交提案到上限。反例：1的Q05仍完整安抚，Q06的公平补记主旨未消失；Q02在1才出现首句甲更多/相等冲突。词语侵入不等于所有任务框架都被替换。

##### L22 / N3956

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-624)

已读 Q01–Q08 每题全部六栏。1/16与1/8多保留；Q02在1/4说乙更多/相等并反复订正到128，1/2恢复一致15/15和差距一半解释。1则变浮点/浮力/浮用：Q01仍判闭馆却说“浮点时间范围外”，Q05直接要求算浮力，其余多循环。反例：1/2的其他题仍合题，Q08的“浮动”本身是正常月份描述，不能把低剂量单个相关字词预先算作主题侵入；该点也不是单调增坏。

##### L23 / N10949

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-632)

已读 Q01–Q08 每题全部六栏。低三档多保留；Q02到1/2及1均首句乙更多、后文相等。强剂量的Q01/Q03/Q04/Q05/Q06仍完整合题，Q07延续原版的先建议带伞再缺信息；Q08在1把月份天数写为“除二月外30或28/29天”，并写“一年365年”。反例：高剂量无循环且建议看似自然也可能伴随数值/单位错误；但不能把这种局部错误等同于全部日常沟通损伤。

##### L24 / N9569

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-640)

已读 Q01–Q08 每题全部六栏。前四档多数稳定；Q08在1/4误列4个30天月、2个28/29天月、其余8个31天月，1/2恢复7个31天/1个二月，1也给正确365/366，是中档细节出错而更高档恢复的例子。1的Q02却首句变“甲盒现在更甜”再算15/15；Q01/Q03/Q04/Q05/Q06仍合题，Q07延续原版谨慎携伞建议。反例：没有全题强烈主题，不意味着完全无变化；单个日历恢复也不能定义有益剂量。

##### L25 / N6454

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-648)

已读 Q01–Q08 每题全部六栏。四个新剂量多数保持主旨及格式，Q02到1/2仍相等，Q08到1/2仍365/366。1的Q02出现甲更多/相等冲突及自我更正到上限，Q08说“除闰年外每年有366天”；Q05有“介管”错词。反例：1的Q01/Q03/Q04/Q06仍完整合理，没有循环；更大剂量的失败并非同一种形态或同一题间门槛。

##### L26 / N9197

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-656)

已读 Q01–Q08 每题全部六栏。Q02在1/2先乙更多后订正至上限，到1却干净给15/15，是另一非单调例。Q08的1/4列31天月时漏7月，1/2声称每个月30或31天并漏二月，1进一步错列4月31天且循环。Q05与Q06到1分别出现“过度反1 0”“一相之得”错词，主旨尚在。反例：Q01/Q03/Q04到1仍正常作答，算术题增量恢复与日历解释恶化同时存在，不存在这八题共有的单维强弱排序。

##### L27 / N8521

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-664)

已读 Q01–Q08 每题全部六栏。这个点跨剂量相对平稳，Q01/Q03/Q04/Q05/Q06/Q08在1仍保留任务主旨和可理解结构，Q08前四档与原版文字相同。1的Q02仍先甲更多后相等，并明确纠正、转而批评题目预设，已不是原版一致的直接回答；Q07延续携伞建议。反例：此点说明强剂量未必引发循环，但不能据日常题自然就称整点或整层完全保持能力。

##### L28 / N3435

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-672)

已读 Q01–Q08 每题全部六栏。Q01/Q02/Q04/Q08跨五档都保持主要事实，Q03在高档更直接指向“等待你”并添加周五期限。1的Q05有“轻描淡白”错词，Q06在完整的诚信建议后突然进入“-bash”循环至上限。反例：不能仅凭首句或前半段自然判断1档无损，也不能因为一题尾部循环就认为该点算术/日历同样受损；弱档总体变化以措辞为主。

##### L29 / N3500

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-680)

已读 Q01–Q08 每题全部六栏。五档多数回答均保住原题主旨、数值和两步格式，没有本批前中层那样显眼的主题接管或长循环。Q08前四档与原版一致，1只在月/日措辞略变；Q02在1把颗换成块但15/15正确。反例与不确定性：Q07保留原版先断言携伞的局限，Q03/Q05有措辞变化；这只能说这八题未见同等强的失序，不能推成天然无效通道或全能力保持。

##### L30 / N8937

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-688)

已读 Q01–Q08 每题全部六栏。前四档多数保留任务，1/2在Q03/Q05自然出现“较晚/较重要”等比较词；1的Q01/Q03/Q04/Q05/Q06在原题开头后进入“较”或“较少”循环。Q02的1档先说“甲盒较甜”再纠正15/15；Q07从1/4起把信息不足接成不需要带伞；Q08在1/8与1/4误称仅2个31天月，1/2恢复正确常识，1又把小月统称28/29天。反例：1档Q02/Q07/Q08都正常EOS，没有“较”长循环，不能仅按同通道词偏置推断全部输出相同。

##### L31 / N6056

[本层八组六栏原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-696)

已读 Q01–Q08 每题全部六栏。前几档多数保留任务；1/4的Q08错称2个31天月，1/2恢复28–31天/365–366天；Q02在1/2先甲更多后相等，Q03在1/2改成“我未能及时完成”造成角色转移。1时八题均为外语字串或组合符号的重复，部分保留“小”“甲盒”“第一步”“这个说法不对”开头后失序，全部达到上限。反例：1/2并未提前全题崩溃，Q01/Q04/Q05/Q06还可理解；末层并非统一弱影响区，且本点不能代表整个末层。

##### 读后提炼的线索与边界

- **剂量确实改变同点表现，但不是共同的单调刻度。** L15/Q02在1/16矛盾、1/8正确、1/4再矛盾；L20与L26/Q02在1/2出错而1恢复一致。L24/Q08在1/4细节错、1/2及1恢复。五个离散剂量不能据此定位精确阈值。
- **同点对不同题有不同敏感性。** L12/Q02最低1/16已有明显矛盾，而同点Q01/Q06到1还保留主旨；L28/Q06在完整诚信建议后才出现bash循环，而Q02与Q08一直保住数值。这些对比比“整层什么时候坏”更可直接核查。
- **中间剂量可显出高剂量掩盖的主题轨迹。** L01的1/4是坐姿语境，1/2及1多成单词；L04的1/2出现电化学，1多回声/循环；L17的1/4部分故事化，1/2电影叙述遍及八题，1进一步碎化。这支持跟踪同点的过渡，但不能命名自然功能。
- **后段有较多保留答题结构的点，也有明显反例。** L29跨五档变化较温和；L22在1有浮点/浮力循环，L30有“较”循环，L31有字串循环。每层仅一个点，不能据此界定连续功能区域。
- **低剂量没有自动获得“无损”证明。** 大量低档回答仍合题，但L12/Q02的1/16是直接反例；反过来，有些Q07从原版先断言带伞转为明确缺信息，属于局部更妥当表达，不能一概视为损伤。未新增评分、模型调用或统计发生率。

覆盖：32层、256组六栏均实际读完，共1,536个展示单元；重复原版去重后为1,288份来源（1,024新剂量、256复用dose=1、8原版）。唯一一次工具输出截断涉及L16中段，已单层完整重读。完整原文仍保留生成上限的截断，不以阅读摘要代替；身份覆盖不证明语义解释无误。

[六栏完整原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html#group-448) · [逐组身份及哈希覆盖](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/coverage-9b.json)

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [delivery-r01/export_receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/delivery-r01/export_receipt.json) | {"status": "completed", "mode": "survey"} | {} |
| [monitoring/automation-completion-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/monitoring/automation-completion-r01.json) | {} | {} |
| [monitoring/completion-status-20261027T130618Z.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/monitoring/completion-status-20261027T130618Z.json) | {"stage": "machine_archive_first_reading_complete"} | {"checked_utc": "2026-10-27T13:06:18.176729+00:00", "machine_ended_utc": "2026-10-27T12:53:04.389576+00:00"} |
| [preflight-delivery-r01/export_receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/preflight-delivery-r01/export_receipt.json) | {"status": "completed", "mode": "preflight"} | {} |
| [preflight-r01/2b-shard-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/preflight-r01/2b-shard-0/receipt.json) | {"status": "completed", "mode": "preflight"} | {"started_utc": "2026-10-27T11:33:13.258279+00:00", "ended_utc": "2026-10-27T11:34:15.858982+00:00"} |
| [preflight-r01/2b-shard-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/preflight-r01/2b-shard-1/receipt.json) | {"status": "completed", "mode": "preflight"} | {"started_utc": "2026-10-27T11:33:13.258134+00:00", "ended_utc": "2026-10-27T11:34:18.004157+00:00"} |
| [preflight-r01/4b-shard-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/preflight-r01/4b-shard-0/receipt.json) | {"status": "completed", "mode": "preflight"} | {"started_utc": "2026-10-27T11:34:19.357636+00:00", "ended_utc": "2026-10-27T11:35:38.358698+00:00"} |
| [preflight-r01/4b-shard-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/preflight-r01/4b-shard-1/receipt.json) | {"status": "completed", "mode": "preflight"} | {"started_utc": "2026-10-27T11:34:19.357806+00:00", "ended_utc": "2026-10-27T11:35:44.860970+00:00"} |
| [preflight-r01/9b-shard-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/preflight-r01/9b-shard-0/receipt.json) | {"status": "completed", "mode": "preflight"} | {"started_utc": "2026-10-27T11:35:46.468458+00:00", "ended_utc": "2026-10-27T11:37:30.488899+00:00"} |
| [preflight-r01/9b-shard-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/preflight-r01/9b-shard-1/receipt.json) | {"status": "completed", "mode": "preflight"} | {"started_utc": "2026-10-27T11:35:46.470136+00:00", "ended_utc": "2026-10-27T11:37:39.282897+00:00"} |
| [preflight-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/preflight-r01/controller.json) | {"status": "completed"} | {"started_utc": "2026-10-27T11:33:13.185289+00:00", "ended_utc": "2026-10-27T11:37:40.513297+00:00"} |
| [qualitative-pass-r01/coverage-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/coverage-summary.json) | {"status": "passed"} | {"checked_utc": "2026-10-27T13:02:09.615323+00:00"} |
| [readiness/delivery-verification-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/delivery-verification-r01.json) | {"status": "passed"} | {"verified_utc": "2026-10-27T11:42:02.697064+00:00"} |
| [readiness/eight-question-live-audit-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/eight-question-live-audit-r01.json) | {"status": "passed", "scope": "Read-only running-record snapshot; no new model generation and no interruption"} | {"checked_utc": "2026-10-27T11:57:19.141040+00:00"} |
| [readiness/formal-completion-verification-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/formal-completion-verification-r01.json) | {"status": "passed"} | {"checked_utc": "2026-10-27T12:57:57.917605+00:00"} |
| [readiness/formal-launch-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/formal-launch-r01.json) | {"status": "launched"} | {"started_utc": "2026-10-27T11:46:10.998500+00:00"} |
| [readiness/formal-launch-review-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/formal-launch-review-r01.json) | {"status": "passed", "scope": "Independent read-only formal launch review; no model execution by reviewer"} | {"checked_utc": "2026-10-27T11:46:41.512152+00:00"} |
| [readiness/independent-result-audit-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/independent-result-audit-r01.json) | {"status": "passed", "scope": "Independent local CPU audit of returned GPU preflight artifacts; no GPU, SSH, model loading, content scoring or semantic labeling performed"} | {"created_utc": "2026-10-27T11:39:44.255563+00:00"} |
| [readiness/preflight-launch-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/preflight-launch-r01.json) | {"status": "launched"} | {"utc": "2026-10-27T11:33:13.072311+00:00"} |
| [readiness/remote-completion-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/readiness/remote-completion-r01.json) | {"status": "passed"} | {"verified_utc": "2026-10-27T11:38:12.261052+00:00"} |
| [survey-r01/2b-shard-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/survey-r01/2b-shard-0/receipt.json) | {"status": "completed", "mode": "survey"} | {"started_utc": "2026-10-27T11:46:13.218924+00:00", "ended_utc": "2026-10-27T12:03:00.527756+00:00"} |
| [survey-r01/2b-shard-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/survey-r01/2b-shard-1/receipt.json) | {"status": "completed", "mode": "survey"} | {"started_utc": "2026-10-27T11:46:13.215548+00:00", "ended_utc": "2026-10-27T12:01:58.140478+00:00"} |
| [survey-r01/4b-shard-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/survey-r01/4b-shard-0/receipt.json) | {"status": "completed", "mode": "survey"} | {"started_utc": "2026-10-27T12:03:02.586216+00:00", "ended_utc": "2026-10-27T12:27:44.839102+00:00"} |
| [survey-r01/4b-shard-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/survey-r01/4b-shard-1/receipt.json) | {"status": "completed", "mode": "survey"} | {"started_utc": "2026-10-27T12:03:02.590617+00:00", "ended_utc": "2026-10-27T12:27:45.011786+00:00"} |
| [survey-r01/9b-shard-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/survey-r01/9b-shard-0/receipt.json) | {"status": "completed", "mode": "survey"} | {"started_utc": "2026-10-27T12:27:47.076364+00:00", "ended_utc": "2026-10-27T12:52:13.274937+00:00"} |
| [survey-r01/9b-shard-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/survey-r01/9b-shard-1/receipt.json) | {"status": "completed", "mode": "survey"} | {"started_utc": "2026-10-27T12:27:47.071038+00:00", "ended_utc": "2026-10-27T12:53:00.609511+00:00"} |
| [survey-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/survey-r01/controller.json) | {"status": "completed"} | {"started_utc": "2026-10-27T11:46:12.844467+00:00", "generation_ended_utc": "2026-10-27T12:53:02.200997+00:00", "ended_utc": "2026-10-27T12:53:04.389576+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有3082个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/014-layer-dose-survey-toy-v1-2026-10-27.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27)。未复制模型权重、环境或凭据。
