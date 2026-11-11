# 005．双针拆分与十个局部修复候选

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-10-26T14:06:50.509099+08:00；不能当作全部子运行起止。

**当时的目的与设计**

先在MMLU和ARC-C各32题上比较A、B、AB、五个随机对以及1和0.5剂量，共17条件；随后定位并测试十个候选，每候选64题、六个修复或反向条件。

**实际过程、结果与后来更正**

首轮完成。C01在MMLU由AB的15/32修到24/32，但反向重现仍18/32，与原版相同；C05在连续margin上有开发信号。没有候选在任一任务正确率上同时通过四项必要比较。本章逐候选保留全部结果，后续判断/报告分离方案另列，没有把局部修复写成唯一根因。

**来源身份**：`root-cause-toy-v1-2026-10-26`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：Acupuncture：两针能力损伤的最小因果定位实验

原路径：`docs/root-cause-localization-plan-v1.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/root-cause-localization-plan-v1.zh-CN.md) · [单独阅读副本](../library/f086b6ff5305fc7c.md)；SHA-256：`f086b6ff5305fc7cebd0dc914ceb3b5823e98b4ce1b3e481ed0668cf5c8ffd89`。

---

#### Acupuncture：两针能力损伤的最小因果定位实验

更新日期：2026-10-26。本文覆盖此前根因方案，作为当前唯一的根因实验设计入口。

**状态：方案、执行合同和代码准备已获授权；根因模型运行继续暂停，待 GPU 就绪报告后另获启动指令。已有迁移实验按其自身协议管理。**

##### 1 中心主线与本轮终点

> 两针改变了什么计算 → 这项变化怎样造成能力损伤 → 根据这项计算，在其他模型里寻找对应位置。

本轮先在4B回答：**保持两针存在，只修复一处有限的中间变化，任务能否恢复；不扎两针，只重现这处变化，任务是否受损；这处计算平时负责什么。**

目标是找到1—2个有因果证据的计算环节。“前额叶”是帮助提出问题的类比；实际结果可以是一个头、一个有限子空间或跨层的少量组件，不预设存在连续、独立的脑区。两针也不预设是唯一入口。

本轮优先解释**能力损伤**。内容偏移和停止异常保留为不同现象，不要求同时解释，更不以“低损伤改变行为”作为成功条件。既有[4B能力结果](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/RESULTS.zh-CN.md)是起点；重复跑大面板不是定位步骤。

##### 2 固定起点与最少材料

源模型为 `Qwen/Qwen3.5-4B`，revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`。权重冻结，沿用BF16及现有推理设置：

- B：零起始L13/N7956，负向，先执行。
- A：零起始L14/N8949，正向，后执行。
- 干预在门控MLP激活之后、`down_proj`之前，提示及答案评分位置沿用现有注入规则。
- 每题参考残差尺度只由原版公共提示计算一次，所有条件固定使用，B开启后不重新校准A。剂量1的单针理想写入约为一个参考残差范数；入口少不等于幅度小。
- 复用[数值桥接收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/transfer-toy-v1-2026-10-26/validation-r01/bridge/receipt.json)已覆盖的检查。新修复钩子须验证作用范围，记录实际局部差分并确认未意外关闭针。

| 材料 | 固定用途 |
|---|---|
| 开发64题：MMLU、ARC-C各32题 | 分解两针、筛选和验证候选；可来自已经看过的题 |
| 确认64题：两任务各32题 | 从未用于本项目查看输出、选点或调参的题中确定；冻结解释后才运行 |
| 功能任务32对：开发16对、确认16对 | 围绕最终候选提出的一个具体功能，比较“需要这项计算”和匹配的对照任务 |

抽题不按原版答对、干预答错或输出长短筛选。运行前固定题目ID、顺序、设置和哈希；功能题在第三步提出具体解释后编制，确认题在查看其模型输出前冻结。上述数量是toy预算，不保证统计检验力。

沿用[现有能力评分口径](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/PROTOCOL.zh-CN.md)：MMLU评分候选为带空格的A—D标签；ARC-C评分完整选项并按字符数归一化。各题同时保留：

1. 正确选项分数减去最高错误选项分数，作为连续定位读数；
2. 按原规则选出的答案及是否正确，作为真实任务终点。

两种任务分别汇报，不混合其分数尺度；小样本诊断成绩不直接冒充原正式面板成绩。数学、代码长生成和全部旧24题重放不列入本轮必跑项。旧24题只保留为已见材料，不恢复Q25—Q40。

##### 3 四步主实验

###### 第一步：拆开两针，确定要追踪的损伤

在同一批开发题上比较原版、A、B、AB，主剂量为1。另固定5组同层随机通道对，匹配逐层写入范数、符号和注入位置规则；所有随机组都保留。

回答两个问题：

- 单针分别造成多大变化，联合后又增加了什么？
- 这种能力下降在匹配随机干预中是否也出现？

随机组给出本轮参照，不足以估计全模型罕见事件的精确概率。相近损伤不取消根因问题，但此后不能把“会掉分”称为两点独有性质。

**固定两个剂量：** A、B、AB及原5组随机对均运行1和0.5，原版只计算一次。不按答错题数触发补跑，也不扫描其他剂量。0.5只用于分解诊断，后续候选验证和确认固定剂量1。若仍不能拆开作用，记录“本轮剂量下未分清”。

输出是一张单针、联合及随机对照的分解表。AB接近A不能单独证明B无作用；任何非加性也不直接证明B经过A传播。

###### 第二步：用便宜读数缩小范围

比较同一道题、同一个选项的完全相同前缀；每个条件从头重算KV和递归状态。包含提示位置及评分所需的答案位置，不比较已经自由分叉的两段文本。

从两针之后的可独立干预贡献中筛查：注意力头、实现支持的线性注意力贡献、MLP贡献。B的下游包含L14计算。先做模块级筛查，只对入选模块限定位置和贡献范围，不逐个遍历全部神经元。

以正确选项优势对候选贡献的梯度，乘上原版与AB的贡献差，近似估计局部修复效应。两任务分别按平均预测修复效应排序、等额合并并去重。**最多8个排名候选，加2个从剩余范围固定抽取的候选，共10个进入真实替换。** 这2个是漏检抽查，不证明搜索完整。

每个候选必须写清：改哪个组件的哪部分贡献、作用于哪些位置、预期影响什么后续计算。残差差分大或梯度排名高只提供线索；少量真实替换与近似不符时，不把近似低分当排除机制的证据。

###### 第三步：保留针做修复，去掉针做重现

对入选候选，在开发题上做以下配对操作：

| 条件 | 操作与问题 |
|---|---|
| 局部修复 | AB持续开启，仅把候选的有限贡献换为同前缀原版值；能否减少损伤？ |
| 反向重现 | 原版不扎针，仅换入同前缀AB下的该贡献；能否重现损伤？ |
| 匹配对照 | 每个候选固定一个同类型、同位置数、同维数及相近幅度的无关替换；任意替换是否也有类似作用？ |

整层残差换回原版、直接抵消源注入、移除针或补入答案不算传播机制证据。记录替换的张量、供体条件和位置，避免局部修复实际上重置整个历史状态。

**两项证据一起看：**

- 真实任务：最终选项正确率及逐题答案变化；不能只让答案分数好看。
- 中间关系：事前写明一个预期，在**未被直接替换的后续计算**中检查任务相关变化是否恢复／重现。被换入的张量本身恢复，不构成这项证据。

例如，若候选解释是“指定信息无法被后续计算正确读取”，需要检查指定信息变化是否按预测影响后续读取和回答；不能只看最后正确答案更容易输出。开发阶段可以提出解释，但进入确认前必须明确测量位置、预期方向和反例。

只保留证据最完整的1—2个解释，不要求恢复全部损伤。本轮实现固定“一个模块贡献+有限位置”为一个候选条目，不再追加联合集合搜索。若只有更大的集合可能有效，先报告当前粒度未定位，后续再讨论。

###### 第四步：确认它平时做什么，并在新题上验证

为每个最终解释写一句具体预测，例如：“此贡献参与读取指定位置的信息；两针破坏这一读取关系，因而影响依赖该信息的答案。”

从“读取指定信息、比较候选、按要求报告已有答案”中选择与证据最相关的一个功能任务族，构造32对任务。只改变主要计算要求，尽量匹配信息、长度、词汇及答案格式；16对用于开发，另16对确认。

这些任务对内置内容与答案标签的排列变化，不额外扩展题目预算。若声称修复了读取或比较，必须检验变化跟随任务内容，而非固定的A/B标签；后续未被替换组件的读数也须检验事先规定的任务关系。仅靠近原版激活、正确答案分数上升或固定字母更常输出，不能证明该计算恢复。若只支持标签报告，则按该范围命名。

具体实现为每个基础任务对包含需计算/直接报告、两种标签排列，共4个短评分项；32对共128项，统计单位仍是32对。另用只改相关事实的无针供体做局部替换及匹配随机对照，检验答案是否按事实变化；这增加供体前向，不增加独立题数。只在答案尾部有效或没有可用下游读取组件的候选，在本轮功能预算下不能确认，保留为能力干预线索，不自动换位置挽救。

在无针模型中对候选做有限、任务匹配的替换，并与无关替换比较；结合原版、AB及局部修复，检验上述功能预测。一次置零掉分不能独立命名功能。若只在注入后有作用，报告为“强制扰动的传播环节”，不宣称它平时负责同名功能。

最后冻结候选、替换范围、功能预测及评分，运行确认64题和确认16对功能题。确认阶段不再换题、换位置、选剂量或修改解释。对每个冻结候选保留原版、AB、修复、重现和匹配对照，同时检查任务终点与中间关系。

##### 4 怎样判断结果，以及何时停止

以题目／功能任务对为统计单位，报告配对效应和95%区间；MMLU与ARC-C分别呈现，重复token不增加样本数。确认比较的方向在开结果前写明。两候选均进入确认时，两者完整报告，不事后只挑较好者。

每个解释至少分别报告四项有方向的比较：修复相对AB的改善、该改善超过匹配修复对照的量、重现相对原版的损伤、该损伤超过匹配重现对照的量。任一必要比较区间跨零，记为该部分证据不足；不把“修复多答对2题、对照多答对3题”判作特异修复。两个分数从同一组选项得出，不算两份独立证据；独立的功能关系检查承担另一项证据。

| 结果 | 本轮可说什么 |
|---|---|
| 修复改善任务、重现损害任务，中间关系及无针功能检验也按预测成立，且有匹配对照支持 | 支持一个局部计算环节的因果解释；仍不证明唯一或完整根因 |
| 只有修复有效，或任务改善但中间关系不成立 | 找到有效干预点，尚未解释原损伤路径 |
| 两针和随机对照均造成损伤 | 说明致损入口不唯一；尚不能判断是否同一机制，共同路径主张需要另做路径检验 |
| 开发有效、确认不支持，或区间过宽 | 解释未获确认或证据不足，不用“不显著”宣称完全无效 |
| 10个候选预算内未定位 | 报告本轮未找到；停止本轮，不据此断言不存在机制 |

本轮首先报告带区间的效应，不预设“解释70%”之类达标数字。若仅连续得分变化而正确率没有可靠改善，保留为定位线索。声称一项“基本不变”时，另需在确认前约定有实际意义的等价范围；不以不显著代替等价。

定位到有作用的传播环节，不等于找到最早发生故障的位置。选择题上的解释不自动覆盖数学或代码；AB的路径不自动代表两针单独的共同路径。上述更强主张不纳入本轮结论。

“有多大”先报告已验证贡献涉及的层、组件、位置及维数。找到有效集合之后，才考虑逐个移除以收紧范围；不先跑1/2/4/8的全套规模曲线，也不把最小已测试集合叫作全模型最小脑区。

##### 5 只在触发时补的检查

| 何时遇到问题或需要更强主张 | 才补什么 |
|---|---|
| 功能任务内置的标签排列仍不足以区分内容与报告偏置 | 只对该歧义补一组事先明确的任务对，不扩大到通用行为评测 |
| 要声称两针的传播路径具有特殊性 | 增加不同损伤来源的局部修复比较；普通掉分的随机对照不能代替路径对照 |
| 修复有效但重现失败，或中间变化与任务结果冲突 | 针对这一冲突检查补偿、替换范围或一条关键连接；不铺开全模型逐边搜索 |
| 已找到有效组件集合，需要更精确边界 | 在该集合内逐个移除；保留随机匹配，不穷举全模型 |
| 已确认解释，需要量化广泛能力影响 | 最终修复／重现及必要对照运行现有四项大面板；可复用设置完全一致的基线 |

内容、EOS、自然激活钳位、全面剂量曲线不作为定位能力损伤的必经阶段。有证据指向其中某项时再提出对应检查。触发检查也需先写清能区分的两个解释和有限预算，不能因它便宜就自动追加。

##### 6 从4B解释走向其他模型

4B得到经确认的计算关系后，再制定9B、2B的有限机制验证：用共同功能任务找对应计算，事前预测它怎样受损、局部恢复应改善什么，并在目标模型检验。**先迁移功能预测，再判断位置对应；不搬编号，也不只比较是否都掉分。**

既有迁移实验属于独立证据，不因本轮方案变更重跑。其他模型出现不同机制也是有效结果。跨模型机制验证和大面板是后续范围，不计入本轮4B最小定位实验。

##### 7 交付与执行边界

本轮获准运行后的交付只有四项：两针分解表、最多10个候选的完整验证记录、最终1—2个解释的新题确认、明确到计算关系的后续迁移预测。原文、失败及未完成记录均保存。

执行前只需落实题目清单、候选筛选规则和钩子验证，不新建通用实验平台。成本包含加载、前反向、真实替换、评分与归档；获准后用代表性工作量测量，不提前承诺分钟级完成。

设计借鉴见[HanLab原论文核查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/literature/hanlab-mechanism-primary-audit-2026-10-26.zh-CN.md)及[原帖第二轮材料](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/literature/lyra-x-thread-round2-2026-10-26.zh-CN.md)：保留能区分解释的对照、真实终点和有限失败结论，将不影响当前判断的扩展后置。

执行定义、冻结清单与操作入口见 [toy 执行合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/CONTRACT.zh-CN.md)。准备工作可完成代码、CPU检查、数据冻结和远端部署；真实模型前向／反向仍须等启动指令。旧根因正文不另存副本；已完成实验的原始证据不受影响。

---

### 原件 2：Acupuncture 两针能力损伤定位：执行合同

原路径：`experiments/root-cause-toy-v1-2026-10-26/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/CONTRACT.zh-CN.md) · [单独阅读副本](../library/f3441c68ff00d907.md)；SHA-256：`f3441c68ff00d907da7b489a55591738adec2fa90559f05dbf0c3a65cc78f69d`。

---

#### Acupuncture 两针能力损伤定位：执行合同

日期：2026-10-26。对应唯一[主方案](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/root-cause-localization-plan-v1.zh-CN.md)。这是方案补完与代码准备的执行定义，不是已完成的根因结果。

**当前授权：完善方案、冻结合同、写代码、CPU验证、部署和报告 GPU 就绪。真实模型前向、反向和正式采集仍等用户启动指令。** 启动时不修改本合同里的科学设置；启动授权记录进入新运行收据。

##### 1 本轮只回答一个问题

两针造成的能力损伤，是否经过一项可单独干预的后续计算？两针保留时修复该贡献，任务是否改善；原版中重现该贡献的变化，任务是否受损？若这两个方向都成立，再检验它平时参与什么计算。

结果最多支持1—2个局部因果解释。传播环节不等于最早故障、完整根因或一个天然连续的“前额叶”。选择题结果不自动解释数学、代码、伤害性内容或不能停止。

##### 2 不变的实现条件

- 源模型固定 Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`；BF16、eager、batch=1、权重冻结、每次前向重算状态。复用既有 `TransferEngine` 的模型加载、分词、参考尺度与原生通道加法。
- B为L13/N7956负向；A为L14/N8949正向。参考尺度只由原版公共提示计算一次，其他条件复用；针持续覆盖评分输入位置。
- 不改永久权重，不训练，不长生成，不跑旧24题或Q25—40，不重复迁移/大Benchmark。
- 代码与题目由 `freeze.json` 绑定；运行收据同时保存输入文件哈希、环境、模型身份、阶段、计时、技术失败和输出哈希。任何失败保留目录，新尝试用新目录，不覆盖半成品。
- 仅一张GPU、一个模型进程起步；不启用复杂多进程调度，不抢占其他作业。

##### 3 材料和预算

| 项目 | 固定预算与用途 |
|---|---|
| 开发选择题 | 64题：MMLU、ARC-C各32，复用已见的诊断集 |
| 确认选择题 | 64题：两任务各32，排除项目已执行/已选用材料；具体排除来源与哈希见数据清单 |
| 第一步 | 原版1条件；A、B、AB和5组随机通道对各运行剂量1与0.5，共17条件、1,088题—条件单元 |
| 筛选 | 原版/AB同前缀，按模块贡献和有限位置计算梯度近似；不遍历全部通道 |
| 真实验证 | 最多10条候选：8条排名候选+2条剩余候选抽查。每条修复、重现及各自匹配对照4条件 |
| 最终解释 | 最多2条，允许0条；本实现不追加联合集合搜索 |
| 功能任务 | 选择1个任务族，32个基础任务对，开发/确认各16。每对包含需计算/已有答案对照，并各做两种标签排列：每对4个短评分项，总计128项；统计单位仍是任务对 |

MMLU按带空格的A—D标签似然评分，ARC-C按完整选项似然/字符数评分，沿用已冻结的能力评分口径。保留选项原始得分、正确选项减最高错误选项的优势、最终选择与正确性。任务分别汇报，不混合分数尺度。

确认题的“未见”仅指本项目可核对的归档和选题记录，不声称模型预训练未见过。功能题族的模板可提前实现，选择哪族与哪个解释配对必须在开发证据之后、确认输出之前冻结。不会把三个任务族全部跑一遍挑结果。

##### 4 四阶段的可执行规则

###### 4.1 拆针

固定运行两个剂量，不使用“答错28题再补剂量”的分支。随机对固定同层、同符号、同逐层写入范数和同位置规则，随机种子写入机器合同；不得按其回答重新抽样。

报告A、B、AB与随机对照的正确率和连续读数。AB接近A不直接证明B无作用；非加性也不直接证明两针相互传递。

###### 4.2 缩小搜索范围

实现粒度固定为L14注意力贡献、L15—31注意力或MLP贡献；不是整个层的残差。L13/L14被注入的MLP不作为修复目标，避免把直接消针当传播解释。

每个模块只考虑公共提示最后位置、评分答案尾部位置两种范围；单token选项的答案尾部为空，不能制造第二个重复候选。所有供体/受体使用同一选项输入和同一位置，重算状态，不混用自由生成的两段文本。

AB下正确项优势的梯度乘以原版减AB的贡献差，估计局部修复。最高错误项先在AB下确定，求导时保持身份。两个任务分别排序，以交错方式等额取前8个去重候选，再固定抽2个未入选候选。排序只提供开发线索。

每条候选身份是“组件+位置范围”，保存实际维数、位置数、数据与排序文件哈希。无论正负结果全部保留。10条用完即停止，不因结果不显著增加预算。

答案尾部为空的题记为未操作，保留在固定题数分母；不按非空位置筛题。只在答案尾部有效的候选，或已无可用后续读取组件的末端候选，不能在本轮单token功能题上确认；可以保留为能力干预线索，不能临时换位置或新造任务挽救。

###### 4.3 真正修复和重现

- 修复：AB保持开启，把候选的有限输出贡献换为同前缀原版值。
- 重现：原版无针，把同一贡献换为同前缀AB值。
- 匹配修复/重现对照：相同组件、位置、维数，将替换增量改成固定随机方向，逐位置匹配增量范数；种子固定。它检验是否任意同幅度替换也有效，不宣称是另一条真实自然通道。

保存针是否开启、供体/受体、替换位置、实际差分和控制差分范数。原值换回原值必须无变化；异常时钩子清理，不污染后续条件。

开发阶段可以记录后续未替换组件的响应用于提出功能假说。进入确认前，必须冻结一个具体的内容依赖关系、读取组件/位置和读数定义。仅“激活更像原版”不合格。读取组件不能就是被替换组件，必须在其后执行；不允许给正确标签定一个方向后声称读取恢复。

###### 4.4 冻结解释后确认

人工依据开发记录选0—2条解释，写明具体功能预测、反例、读取位置、方向及开发读数来源。程序检查候选属于已完成验证的预算、文件哈希一致、功能开发记录存在，才允许进入确认。

功能任务从读取信息/比较/报告给定答案中只选1族。内容与答案标签排列分开，检验改善跟随内容还是固定字母。无针条件下，比较同内容“需要该计算”和“答案已经给出”的匹配任务，以及局部重现/对照。功能名由这些证据限制，不由组件位置或词表投影决定。

功能任务另带一条只改相关事实的供体提示：在无针模型中，将该供体的候选贡献换入原提示，并做同幅度随机方向对照。它新增供体前向和两个替换条件，不新增独立问题或长生成。要求输入长度与替换位置可核对，否则技术检查失败；依赖计算的任务预测转向供体事实，明确给出的答案对照预测保持原答案。相关变化在后续未替换组件上按冻结读数检查。

确认64题和确认16对功能题在冻结之后运行。每个解释保留原版、AB、修复、重现及两种匹配对照；记录未直接替换的读取关系。两候选均完整报告。读数不能证明具体功能时，只报告传播环节。

##### 5 判据必须能被反例推翻

每个任务分开计算四个有方向的逐题差值：

1. 修复减AB；
2. 修复减匹配修复对照；
3. 原版减重现；
4. 匹配重现对照减重现。

以正确性为确认主终点，连续优势用于筛选和解释。按题/基础功能对配对bootstrap，固定10,000次、95%区间。四项必要比较下界均大于0才支持对应的双向、超出匹配替换的任务效应；区间跨零记为证据不足。不把“修复多答对2题、对照多答对3题”算成功，不把连续得分和正确率当两份独立证据。

这只是任务效应的判据。机制解释还须有预先冻结的未替换读取关系和内容/标签检验支持。小样本可能无法确认，不能追加题目追显著性。两最终解释同时报告，各自按预定四项比较解释，不宣布全模型唯一发现或家族错误率已控制。

| 观察 | 结论限制 |
|---|---|
| 双向任务效应、匹配对照及功能关系都支持 | 支持该局部传播计算的解释 |
| 只有修复有效 | 有效修复点，尚未解释原损伤路径 |
| 只跟随答案标签 | 报告输出/标签效应，不命名读取或比较功能 |
| 仅连续分数变化 | 定位线索，不宣称能力恢复 |
| 区间过宽、开发与确认冲突 | 证据不足或解释未确认 |
| 10条内无候选支持 | 本轮未定位；停止，不否定机制存在 |

##### 6 就绪验收和开跑后的首关

准备阶段完成：数据/代码/合同冻结；CPU合成检查覆盖位置、范数、梯度近似、供体方向、统计和确认门槛；远端相同环境导入与CPU检查；GPU/模型文件只读清点。此阶段不加载模型。

获准开跑后先用固定开发题中的代表性小批量检查真实模型：干净评分与冻结旧实现一致、原值恢复无变化、针在修复时仍存在、梯度有限、替换范围/控制范数合格。失败即停止并保留证据；通过才进入17条件采集。不把合成CPU测试当作这道模型检查已通过。

计时从加载开始，分别记录校准、前向、反向、供体、替换、评分与归档；先实测，再给ETA。不承诺几秒或十分钟。

`run_root.py`各阶段需要显式执行开关和新的输出目录。准备就绪不自动运行、排队或创建周期任务。大Benchmark、跨模型机制确认和任何额外干预不包含在本次准备合同内。

---

### 原件 3：Acupuncture 根因 toy 首轮结果

原路径：`experiments/root-cause-toy-v1-2026-10-26/RESULTS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/RESULTS.zh-CN.md) · [单独阅读副本](../library/d660bf94e4e2209c.md)；SHA-256：`d660bf94e4e2209cb223b6cb0952296d7dcd40a15a651a421de9fa61df64e627`。

---

#### Acupuncture 根因 toy 首轮结果

首轮于北京时间 **2026-10-26 15:48:44** 完成。拆针64题、排序64题、10个候选各64题及六种条件全部完成；双卡正式运行技术错误为0。两张卡各完成5个候选、320条记录，均正常退出并释放。两端完整性核验通过，1,499个证据文件已取回，包含旧单卡中断记录和双卡分片、聚合副本。

**结论：找到开发阶段的局部修复与连续得分线索，尚未确认导致原损伤的具体计算或“前额叶”。** 正确率上没有任何候选在任一任务中同时通过四项必要比较。此结论不是模型执行失败，也不否定未测试路径存在。

##### Material Passport

- Origin Skill / Mode：academic-research-suite / experiment-agent validate。
- Origin Date：2026-10-26；Version Label：first-round-r01。
- Verification Status：ANALYZED（既有统计核对；本次收尾未重新运行模型）。
- 技术完整性：服务器及本地 `parallel_validate.py verify` 均返回 completed；归档哈希通过。
- 数据范围：冻结开发集，两任务各32题；独立确认集和功能确认均未运行。
- 完整结构化读数：[first-round-results.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/first-round-results.json)；导出程序：[collect_first_round_results.py](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/collect_first_round_results.py)。

##### 拆针与随机对照

以下是各32题中的答对数；不能与此前不同样本量的正式Benchmark成绩直接作百分点对比。全部原始配对区间保存在结构化读数中。

| 条件 | MMLU | ARC-C |
|---|---:|---:|
| 原版 | 18 | 18 |
| A，剂量1 | 17 | 12 |
| B，剂量1 | 15 | 14 |
| A+B，剂量1 | 15 | 12 |
| 随机R01，剂量1 | 9 | 5 |
| 随机R02，剂量1 | 2 | 11 |
| 随机R03，剂量1 | 11 | 10 |
| 随机R04，剂量1 | 4 | 9 |
| 随机R05，剂量1 | 12 | 14 |
| A，剂量0.5 | 15 | 16 |
| B，剂量0.5 | 12 | 15 |
| A+B，剂量0.5 | 17 | 17 |
| 随机R01，剂量0.5 | 16 | 11 |
| 随机R02，剂量0.5 | 2 | 17 |
| 随机R03，剂量0.5 | 10 | 16 |
| 随机R04，剂量0.5 | 7 | 17 |
| 随机R05，剂量0.5 | 16 | 16 |

随机通道对也会损伤这一开发面板，当前结果不支持“只有原两点能造成损伤”。A、B、AB的效应不能只用这些正确率相加解释为交互机制。

##### 全部10个候选

四项依次为：修复−AB、修复−匹配修复对照、原版−重现、匹配重现对照−重现。`✓`表示现存95%配对bootstrap区间下界严格大于0，`—`表示未满足。每任务32题、10,000次固定重采样；下表沿用冻结统计，不改阈值。margin是正确选项相对最高错误项的连续优势。

| 候选 | 组件／位置 | MMLU margin | MMLU正确率 | ARC margin | ARC正确率 |
|---|---|---|---|---|---|
| C01 | L23 attention／提示最后位置 | ✓✓✓✓ | ✓✓—— | ———— | ———— |
| C02 | L27 MLP／提示最后位置 | ✓✓—✓ | ———— | ✓✓✓— | ———— |
| C03 | L20 attention／提示最后位置 | ✓✓—— | ———— | ———— | ———— |
| C04 | L24 MLP／提示最后位置 | ———— | ———— | ✓✓✓— | ———— |
| C05 | L19 attention／提示最后位置 | ✓✓✓✓ | ✓✓—— | ✓✓✓✓ | ———— |
| C06 | L22 MLP／答案尾部 | ————* | ————* | ✓——— | ———— |
| C07 | L28 MLP／提示最后位置 | ✓✓—— | ✓✓—— | —✓—— | ———— |
| C08 | L27 MLP／答案尾部 | ————* | ————* | ✓—✓✓ | ———— |
| C09 | L16 MLP／提示最后位置，抽查 | ———— | ———— | ———— | ———— |
| C10 | L15 attention／提示最后位置，抽查 | ——✓✓ | ———— | ✓—✓✓ | ———— |

*MMLU的单token选项没有答案尾部位置，这两项未操作但仍保留在固定分母；零效应不能解释为模块无作用。所有层号为零起始。

具体可讨论的线索：

- C01在MMLU中，把AB的15/32修复到24/32，匹配修复对照为15/32；相对二者均提高28.125个百分点，95%区间为[12.5, 43.75]个百分点。但反向重现仍为18/32，与原版18/32相同。修复分数甚至超过原版，不能把全部增益简单称为恢复原有能力。
- C05在MMLU中修复为19/32，相对AB提高12.5个百分点，[3.125, 25]；相对匹配修复对照14/32提高15.625个百分点，[3.125, 28.125]。反向重现为18/32，正确率尚无损伤重现证据。它在两任务的margin四项比较均有开发信号；ARC正确率仅12/32变13/32，区间仍含零。
- C07也有MMLU正确率修复线索，但连续读数的完整双向比较未满足。两条抽查候选没有通过四项完整比较。

以上候选使用同一开发集排序和观察，未做家族错误率控制；候选阶段共报告160个相关的配对区间，不能把零星过界当作独立确认。确认主终点仍是正确率。**目前没有“完整根因已定位”的结论，也没有依据给这些模块命名具体功能或确定功能区大小。**

##### 实际耗时与空间

| 项目 | 实测 |
|---|---:|
| 拆针 | 18分39.54秒 |
| 排序 | 3分2.17秒 |
| 双卡正式候选实验，含合并 | 53分20.76秒 |
| 首次正式启动14:19:52至完成15:48:44，含单卡转双卡期间 | 88分52.59秒 |
| 双卡worker耗时合计 | 106分21.88秒（进程墙钟之和，不是GPU内核时间） |
| 剩余计算ETA | 0 |

最近预计15:52—16:00，实际提前3分15秒至11分15秒；最初单卡16:37预测提前48分15秒。旧单卡12条部分结果与退出码143完整保留，这次停止是用户授权的调度交接，不计为运行bug。重复的12条没有二次进入最终统计。

15:54检查：工作盘可用136.3 GiB；模型盘与临时盘为同一文件系统，可用43.7 GiB，不能重复相加；本地归档盘可用约877.4 GiB。双卡结果目录50.6 MiB，完整证据包解压约59.4 MiB，空间充足，未删除其他材料。

证据：[服务器完成与打包收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/monitoring/first-round-completion-20261026.json)、[本地归档核验](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/monitoring/local-archive-verification-20261026.json)、[最终进程与磁盘快照](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/monitoring/20261026T075455Z.json)、[聚合收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/receipt.json)。归档SHA-256为`7f98357c2165f6c20dc9e7564e3a33d568123d0abc42dafa2dc812e0bac0fe95`。

##### 统计解释核对

11/11项已检查：分任务报告避免聚合方向掩盖差别；不从小面板推及全部能力；明确开发选点带来的选择偏差；未按干预后的成功/失败筛题；不把候选命中率当总体普遍率；不把极端排名的再测当独立复制；10候选及全部负结果保留；160个区间不宣称多重比较受控；不事后改剂量、预算或阈值；真实替换支持其操作条件下的作用但不自动说明自然功能；模型执行先于输出，仍不把后层修复点等同最早损伤来源。

##### 本轮边界

半小时巡检已设为PAUSED，保留配置。停止在开发候选实验完成处，没有启动功能开发、独立确认、新模型机制实验或大Benchmark。C05/C01可作为后续讨论材料，但仍须形成并冻结具体功能假说、未替换的后续读取关系及反例；本轮不自动编造这两条解释。

---

### 原件 4：根因 toy：本轮执行状态

原路径：`experiments/root-cause-toy-v1-2026-10-26/EXECUTION.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/EXECUTION.zh-CN.md) · [单独阅读副本](../library/3e8bfaf77075acac.md)；SHA-256：`3e8bfaf77075acac8fff37a29c4087df38d62e1b5d412feb5c3b829ec07bdceb`。

---

#### 根因 toy：本轮执行状态

2026-10-26 用户已明确授权完成检查、报告 ETA 后在空闲 GPU 启动。授权原文见 [启动授权](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/launch-authorization-20261026.json)。这覆盖此前的模型暂停；实验设置仍以冻结合同为准。

##### 当前：首轮已完成，监控已暂停

北京时间 **2026-10-26 15:48:44** 完成。原拆针与排序各64题、双卡各5候选及320条记录全部齐全，worker退出码均0；服务器与本地聚合核验通过，完整证据1,499文件已取回。双卡候选阶段实测53分21秒；自首轮正式启动计88分53秒（含交接）。剩余ETA为0。工作盘可用136.3 GiB，模型/临时盘43.7 GiB，本地约877.4 GiB，空间充足。

首轮有局部修复和连续得分线索，正确率没有候选同时通过四项必要比较，不能称为根因已定位。见[首轮结果与完整证据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/RESULTS.zh-CN.md)。本次半小时巡检已PAUSED，功能解释和独立确认未自动启动。

##### 双卡运行历史

用户随后授权“拆重双卡吧，把资源用满”。北京时间 **14:55:24** 已启动两张 H20：GPU 0 处理 C01—C05，GPU 1 处理 C06—C10，每个候选均为冻结的 64 题、六种条件。这里的“候选验证”就是正式的修复、重现与匹配对照实验，不是启动前的软件检查。拆针与排序已分别在 14:38:31、14:41:34 完成，继续复用。

只把同时运行的模型进程由一个改为两个，模型、题目、校准、剂量、数值精度、随机种子和科学实现不变。原冻结文件和历史收据保持不变；[双卡授权](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/parallel-authorization-20261026.json)及[分片执行代码](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/parallel_validate.py)单独绑定执行修订。新目录为 `runs/root-parallel-r01`，旧目录为 `runs/root-r01`。

- 单卡旧候选进程于 14:43:49 按用户授权停止，保留 12 条已完成记录和退出码 143；这是双卡交接，不是实验失败。C01 的这 12 条在新批次重算，额外成本保留记录，最终统计只使用新批次。
- 双卡代码 CPU 测试 **36/36** 通过；此前一处过时测试字段检查已修正，失败日志与通过日志均保留。GPU 1 对两道题的全部六条件重算与 GPU 0 原记录完全一致，该检查用时 **26.35 秒**。
- 15:01 快照：两边各完成 **37/320** 条候选题目记录，共 **74/640（11.6%）**，均持续产出，无运行报错；工作盘可用 **136.4 GiB**，模型/临时盘 **43.7 GiB**。见[最新快照](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/monitoring/root-parallel-r01-live.json)。
- 双卡启动前给出的候选阶段 ETA 为 **57—65 分钟**，对应约 **15:52—16:00** 完成；基线为单卡候选阶段 113.2 分钟按两卡均分。此 ETA 覆盖当前正式候选实验及汇总，不包括之后尚未冻结的功能解释和独立确认。

两个 worker 分别落盘，再核验候选互斥覆盖、每个候选全部 64 题及六条件、题目身份与全部文件哈希后合并。合并阶段为 `validate-parallel`，必须经 `parallel_validate.py verify` 验证，不能冒充旧单卡 `validate` 收据直接进入下一阶段。两张卡已经正式运行，后续只在发现真实技术问题时修复，不追加与当前运行无关的预检。

##### 已通过的检查

- 目标服务器 CPU 测试 26/26 通过，无跳过；[日志](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/readiness/server-cpu-tests-r02.txt)。
- 权重、分词器、运行库、冻结文件核验通过；[服务器验收](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/readiness/server-ready-r02.json)。
- 固定功能数据的 1,536 个选项/供体组合分词对齐通过。
- 真实 4B 模型预检 46.11 秒通过：旧评分一致、原值替换一致、真实局部替换保留两针、替换范围与幅度合规、梯度有效，结束后权重未变且钩子移除；[完整收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-r01/preflight-r01/receipt.json)。

首个服务器清点曾因部署目录缺少历史身份文件失败，完整保留 [首轮清点](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/readiness/server-check-attempt1.json)。已改为使用本次准备包中的同一资产哈希，重新冻结；没有改变题目、剂量、模型或计算方法。旧准备冻结保留在 [preparation-freeze-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/readiness/preparation-freeze-r01.json)。

##### 最初单卡启动记录

- 主机：`gqa-h20`；GPU：H20 0。
- 目录：`/workspace/acupuncture/experiments/root-cause-toy-v1-2026-10-26/runs/root-r01`。
- 启动：北京时间 **2026-10-26 14:19:52**（UTC 06:19:52）。
- 冻结 SHA256：`bc612fb814bda7eb4da07d93d70c18b93e6bda1722c113436cd6824ff2fdafc3`。
- 顺序：`decompose-r01` → `rank-r01` → `validate-r01`；每阶段核验前序完整收据，失败即停。启动脚本见 [pipeline-r01.sh](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-r01/pipeline-r01.sh)。
- 启动复核：首个 worker PID 1534290；已输出 3/64 题的全部条件记录，GPU 0 占用 9,471 MiB，GPU 1 空闲。此为启动快照，不代表持续实时状态。

##### 最初单卡启动前 ETA（已被双卡更新替代）

已在正式启动前向用户报告。依据本机真实预检、实际分词长度和服务器统计计时，单 GPU 依当前代码顺序执行：

| 阶段 | 预计分钟 |
|---|---:|
| 拆开两针与匹配随机对照 | 20.2 |
| 梯度候选排序 | 3.3 |
| 最多 10 个候选的真实修复、重现及对照 | 113.2 |
| 合计 | **136.7** |

首轮预计北京时间 **16:37 左右**结束；敏感性范围 **16:18—16:59**（118—159 分钟），不是统计置信区间。没有按倍数加安全垫。含各阶段加载、正式计算及统计，不含尚未发生的技术故障、后续人工解释决策和归档。测量与推算见 [ETA 凭证](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/readiness/eta-before-launch-r01.json)。

功能开发与独立确认没有自动排入本脚本：先根据已完成的候选验证写出最多 1—2 个可检验解释，再按合同冻结后确认；没有支持就记录未定位。当前尚无根因结果，预检通过不是科学假设得到支持。

##### 半小时巡检

用户已授权每30分钟检查进度、ETA及磁盘空间，并立即修复发现的技术bug。当前聊天心跳 `acupuncture`（Acupuncture 根因实验半小时巡检）已启用。每次均报告；失败记录和原运行保留，实现修复后按冻结与前序收据约束在新目录验证续跑。不得为获得结果修改实验设置。首轮完整交付后停用本次巡检。

首个[监控快照](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/monitoring/20261026T062706Z.json)：北京时间14:27，拆针29/64题，持续产出，无报错；输出约4.7 MiB，远程输出盘可用约147.1 GiB，模型/临时盘约43.7 GiB，空间充足。ETA暂沿用实测基线16:37，后续按各任务、阶段实测速率更新。

---

### 原件 5：执行入口与交接

原路径：`experiments/root-cause-toy-v1-2026-10-26/RUNBOOK.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/RUNBOOK.zh-CN.md) · [单独阅读副本](../library/e96409df9be3edc8.md)；SHA-256：`e96409df9be3edc8da275cd8e9ca1a6d8fe9996f026343c0805009a3c6b6d4bc`。

---

#### 执行入口与交接

主定义见[执行合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/CONTRACT.zh-CN.md)，机器设置见[contract.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/contract.json)。没有启动授权文件，入口会在加载模型前退出。

##### 准备阶段

在本目录运行 CPU 检查和冻结核验：

```sh
python -m unittest discover -p 'test_*.py' -v
python freeze.py verify
```

需要已有 PyTorch 的解释器。纯Python检查可以单独运行，但缺PyTorch而跳过的张量测试不算完整验收。本次本地CPU运行库为PyTorch 2.7.1；目标服务器为已固定的2.6.0+cu124，不能将本地通过冒充目标环境验证。

`check_ready.py --output <新收据路径>`只清点目标环境、权重哈希、分词对齐和GPU状态，不加载模型。它需要在已部署的新目录中运行；输出仅表示检查时刻可用，不占用或预留GPU。

##### 获准后的运行顺序

每阶段使用新输出目录。`--prior`可重复。启动授权文件必须记录用户真实指令、授权时间、本实验名称和`status=authorized`；准备阶段不伪造该文件。

| 阶段 | 入口参数 | 必需的已完成收据 |
|---|---|---|
| 实际模型预检 | `--stage preflight` | 无；验证真实模型评分、梯度和修复钩子 |
| 拆针 | `--stage decompose` | preflight |
| 排名 | `--stage rank` | preflight、decompose |
| 有限候选真替换 | `--stage validate` | preflight、rank |
| 功能开发 | `--stage function-dev --explanations proposal.json` | preflight、validate |
| 新题确认 | `--stage confirm --explanations final.json` | preflight、validate、function-dev |

各模型阶段共同需要：

```sh
python run_root.py --stage <阶段> --execute \
  --launch-authorization <实际用户启动授权.json> \
  --model /data/models/Qwen3.5-4B-851bf6e --device cuda:0 \
  --output <新的阶段目录> --prior <前置阶段receipt.json>
```

这是参数说明，不是自动启动脚本。模型预检失败时不进入采集；失败目录完整保留。代码修复需另行冻结并从受影响的阶段重新开始，不能修改旧输出。

##### 两处有意保留的研究决策

开发结果出来以前不能知道哪个候选有用、负责什么功能，所以程序不会自动编造结论。

`proposal.json`需包含：`family`（reading/comparison/reporting中选1），`validation_receipt_sha256`，以及1—2项`explanations`。每项写入已测试的`candidate_id`与`candidate_sha256`、`hypothesis`、`task_relation`、`expected_direction`、`falsifier`，以及未替换下游`reader`的组件和`positions=prompt_last`。开发提案不得预填投影。

功能开发只用clean开发输入学习预定内容分组`[1,1,-1,-1]`的均值差读数，记录来源哈希。这是内容相关读数，不自动命名功能；真实供体替换、任务终点、标签排列对照仍须一起看。

`function-dev`产生`explanations.frozen.json`。收据完成后，使用`freeze.py seal`将其绑定到该收据，生成新的最终确认输入。确认程序检查它与开发输出完全一致；不能在确认后修改位置、投影或任务族。

若没有候选通过或无法写出可检验的功能预测，本轮可以在开发验证结束，不需要凑足两条解释。只在答案尾部有效或没有下游读取位置的候选，按合同保留能力干预线索。

##### 如何看结果

逐题JSON保留完整选项得分、实际来源针偏移、局部替换范数、输入哈希和钩子范围。`summary.json`报告配对效应；功能结果另按计算要求、两种答案标签排列和内容读数分别报告。汇总不会自动把“分数好看”标为找到根因。

确认集仅64题、功能确认仅16个基础对，区间可能较宽；这是允许的失败结论，不是继续加样本或筛除失败题的理由。真实模型预检和正式结果均不在准备完成收据内冒充已通过。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [data/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/data/verification.json) | {"status": "passed"} | {} |
| [first-round-results.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/first-round-results.json) | {"status": "completed_development_results_not_mechanism_confirmation"} | {} |
| [launch-authorization-20261026.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/launch-authorization-20261026.json) | {"status": "authorized", "scope": "Complete technical checks including a small real-model preflight; report measured ETA before starting the formal root-cause stages, and start on an idle GPU. Preserve frozen scientific settings and confirmation gates."} | {"granted_at": "2026-10-26T06:02:09.954217+00:00"} |
| [monitoring/first-round-completion-20261026.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/monitoring/first-round-completion-20261026.json) | {} | {"verified_at": "2026-10-26T07:57:17.525817+00:00"} |
| [monitoring/local-archive-verification-20261026.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/monitoring/local-archive-verification-20261026.json) | {"status": "archive_hash_verified_and_extracted"} | {"checked_at": "2026-10-26T07:59:51.532365+00:00"} |
| [monitoring/root-parallel-r01-controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/monitoring/root-parallel-r01-controller.json) | {"status": "running"} | {"started_at": "2026-10-26T06:55:24.037805+00:00"} |
| [readiness/cpu-tests.receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/readiness/cpu-tests.receipt.json) | {"status": "passed"} | {"checked_at_utc": "2026-10-26T05:56:39.144455+00:00"} |
| [readiness/engine-cpu-tests.receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/readiness/engine-cpu-tests.receipt.json) | {"status": "passed"} | {"checked_utc": "2026-10-26T05:44:14.664611+00:00"} |
| [readiness/eta-before-launch-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/readiness/eta-before-launch-r01.json) | {"status": "measured_preflight_extrapolation_not_a_completion_claim"} | {"created_at": "2026-10-26T06:18:15.040631+00:00"} |
| [readiness/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/readiness/receipt.json) | {"status": "local_prepared_remote_deployment_awaiting_explicit_approval"} | {"reported_at_utc": "2026-10-26T05:57:42.292027+00:00"} |
| [runs/parallel-gpu1-check-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/parallel-gpu1-check-r01/receipt.json) | {"status": "completed", "stage": "parallel-gpu-check"} | {"started_at": "2026-10-26T06:47:14.062737+00:00", "finished_at": "2026-10-26T06:47:40.415268+00:00"} |
| [runs/root-parallel-r01-controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01-controller.json) | {"status": "completed"} | {"started_at": "2026-10-26T06:55:24.037805+00:00", "finished_at": "2026-10-26T07:48:44.799977+00:00"} |
| [runs/root-parallel-r01/C01/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/C01/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/C02/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/C02/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/C03/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/C03/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/C04/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/C04/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/C05/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/C05/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/C06/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/C06/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/C07/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/C07/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/C08/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/C08/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/C09/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/C09/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/C10/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/C10/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/receipt.json) | {"stage": "validate-parallel", "status": "completed"} | {"finished_at": "2026-10-26T07:48:44.435481+00:00", "started_at": "2026-10-26T06:55:24.087973+00:00"} |
| [runs/root-parallel-r01/shard-0/C01/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/shard-0/C01/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/shard-0/C02/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/shard-0/C02/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/shard-0/C03/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/shard-0/C03/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/shard-0/C04/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/shard-0/C04/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/shard-0/C05/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/shard-0/C05/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/shard-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/shard-0/receipt.json) | {"stage": "validate-shard", "status": "completed"} | {"started_at": "2026-10-26T06:55:24.087973+00:00", "finished_at": "2026-10-26T07:48:28.117208+00:00"} |
| [runs/root-parallel-r01/shard-1/C06/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/shard-1/C06/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/shard-1/C07/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/shard-1/C07/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/shard-1/C08/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/shard-1/C08/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/shard-1/C09/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/shard-1/C09/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/shard-1/C10/ability-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/shard-1/C10/ability-summary.json) | {} | {} |
| [runs/root-parallel-r01/shard-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-parallel-r01/shard-1/receipt.json) | {"stage": "validate-shard", "status": "completed"} | {"started_at": "2026-10-26T06:55:24.089202+00:00", "finished_at": "2026-10-26T07:48:41.944084+00:00"} |
| [runs/root-r01/decompose-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-r01/decompose-r01/receipt.json) | {"stage": "decompose", "status": "completed"} | {"started_at": "2026-10-26T06:19:52.211386+00:00", "finished_at": "2026-10-26T06:38:31.750638+00:00"} |
| [runs/root-r01/decompose-r01/summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-r01/decompose-r01/summary.json) | {} | {} |
| [runs/root-r01/launch-verification-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-r01/launch-verification-r01.json) | {} | {"checked_at": "2026-10-26T06:22:40.142115+00:00", "started_at": "2026-10-26T06:19:52Z"} |
| [runs/root-r01/preflight-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-r01/preflight-r01/receipt.json) | {"stage": "preflight", "status": "completed"} | {"started_at": "2026-10-26T06:06:50.509099+00:00", "finished_at": "2026-10-26T06:07:36.622391+00:00"} |
| [runs/root-r01/rank-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-r01/rank-r01/receipt.json) | {"stage": "rank", "status": "completed"} | {"started_at": "2026-10-26T06:38:32.538582+00:00", "finished_at": "2026-10-26T06:41:34.707201+00:00"} |
| [runs/root-r01/validate-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/runs/root-r01/validate-r01/receipt.json) | {"stage": "validate", "status": "running"} | {"started_at": "2026-10-26T06:41:35.512135+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有1549个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/005-root-cause-toy-v1-2026-10-26.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26)。未复制模型权重、环境或凭据。
