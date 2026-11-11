# 030．公开配方小题包复现

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-10-30T19:05:19.151793+08:00；不能当作全部子运行起止。

**当时的目的与设计**

按公开配方目录固定不同配置，用各配方五题、128-token上限采集，并设置原版、零剂量和恢复等参照；来源版本与配方资格分别保存。

**实际过程、结果与后来更正**

实际采集与完整性核验1170条完成；执行时间晚于目录命名日。不能写所有210配置都有效、稳定人格或能力无损；当时完整并排解释报告未完成。预检、校准和原文记录均列入。

**来源身份**：`x-recipe-reproduction-v1-2026-10-29`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：Qwen3.5 4B 公开配方复现

原路径：`experiments/x-recipe-reproduction-v1-2026-10-29/PROTOCOL.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/PROTOCOL.zh-CN.md) · [单独阅读副本](../library/8e0f7358a4d34b23.md)；SHA-256：`8e0f7358a4d34b231507d44ee041ff7ed7a80676489aed329658c74215b592a3`。

---

#### Qwen3.5 4B 公开配方复现

##### 授权与问题

**2026-10-30最新边界：本轮仅完成设计、代码、校准与GPU技术预检。GPU Ready后停止并讨论，不自动启动正式1,170条采集。此前全量授权由此次分阶段要求收紧。正式运行需要另行记录用户批准及冻结哈希的`formal_approval.json`；当前不创建该文件。**

用户于2026-10-29明确授权：复查既有及新增公开人格配方，在4B上全部复现，每个配方五道题、每题128 token，并提交复现报告。随后确认先使用已有记录与公开仓库继续。本轮以公开的完整配置为对象，不按生成是否有趣筛选，也不补猜欠缺的剂量。固定来源合计232条记录，完整条件去重后210个配置，恰1050条干预回答；原版按题目与解码条件共享。

本轮想回答的是：在固定模型、短回答条件下，这些配方会产生哪些可见变化，哪些来源描述能在五个指定场景中观察到？五题不能认证稳定人格、天然功能区或广泛能力保持。

##### 来源与纳入

- 历史来源为本仓库《X线索汇总》和两份结构化配方清单，原件及来源哈希保留。
- 新来源为lyra公开仓库链接的Neuronary配方词典的固定快照，保留公开ID、模型、作者标签、参数、日期、采样设置及链接。社区投稿与lyra本人条目分开标记；公开标签不直接作为功能真值。
- 只执行Qwen/Qwen3.5-4B、坐标/方向/数值完整的静态加法配置。其他模型、不完整参数或没有完成的目标列在排除表中。作者试验性配方、撤回候选和已报告退化的完整配置仍保留，不冒充成功发现。
- 完全相同的坐标、带符号剂量、尺度计算规则和有效解码设置合并来源；同坐标不同剂量、尺度规则或解码设置分别保留。旧原双点±1不被网站的新±0.7覆盖。
- 本次X登录浏览器不可用，公开请求返回403；用户已同意改用已有记录和公开仓库，因此不声称本轮完整重读了新增X评论。

##### 五道题与原版对照

每个配方恰好五题：三个共同的英文问题，覆盖自我描述、简短算术和日常安慰；另两个贴近原帖或该配方所述场景的问题。专属题不要求扮演目标人格，不提示目标风格标签。完整英文提示、中文译文和每配方映射在生成前冻结。

同一题目、同一有效解码设置的原版回答只计算一次，供所有相同条件引用。不同采样/重复惩罚设置的原版独立计算。每次回答都用新上下文、新cache；不在五题之间传递聊天历史。

使用原生聊天模板、单user消息、关闭thinking。最多128个新token，正确EOS可提前停止，达到上限不自动扩到256/1024，不为形成目标输出重试。保留含特殊符号的原始解码、可读文本、完整生成token和停止原因。

##### 模型与干预

模型为Qwen/Qwen3.5-4B，revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`。本轮校验既有12文件资产清单；使用BF16、eager attention、实际batch=1、四CPU线程和当前已验收环境。层和通道编号从零开始。

对每个指定MLP通道，在down_proj输入处施加：

`activation[..., neuron] += dose × fixed_layer_residual_scale / norm(W_down[:, neuron])`

增量按模型BF16舍入，并在prefill和全部decode位置施加；同层多个不同通道同时作用，记录每点请求量、BF16量、实际首位置位移和hook次数。权重不写入，没有训练或静态参数版。

未单独说明尺度的条目使用lyra公开实现的固定参考规范。若作者完整统计文件可取得则保留其身份；否则使用作者明确的固定REFERENCE_TEXT回退：原版纯文本前向，排除首token，逐层计算block输出L2范数的`torch.median`，一次生成全32层尺度，随后冻结供全轮复用。来源及实际采用的路径以`scales.json`为准。固定参考回退不冒充作者私有统计逐值一致。作者明确要求逐提示校准的条目，按其规则另标`normalization`，保存该提示的clean尺度，固定到该题整个生成过程；不与固定参考尺度条目混同。

没有显式解码值的旧配方采用greedy、重复惩罚1。来源明确提供temperature/repetition_penalty或备注里的top_p/top_k/min_p时保留；temperature=0解释为greedy，正温度启用采样，未指定的top_p=1、top_k=0、min_p=0。所有调用重设seed=0；同题两臂使用相同设置和种子，但采样后分叉不构成独立重复。本轮使用Transformers生成器；lyra自定义的CPU逐行随机抽样实现不同，不能保证同温度/种子逐token重放。128上限和关闭thinking是本轮统一设置。重复惩罚在两种实现中都覆盖完整prompt和已生成token。每条实际参数写入记录。

##### 验收与执行

CPU测试验证多点同层加法、padding及decode位置、零剂量、异常撤钩子、权重不变、同解码共享原版、不同解码分开，以及分片覆盖。使用有Torch的服务器环境执行，不把skip算通过。

正式生成前，所用GPU先做原版、零剂量、真实多点、撤钩子后原版的四次短验收，再补足全部10组有效解码的原版/配方配对，以及逐提示校准与同层多通道的代表配置；零剂量及恢复输出须逐token等于其原版。两卡使用相同已冻结尺度。预检是技术验收，单独保存，不混进各配方五题。

最多两个GPU worker；启动前检查真实显存/进程空闲，不中断其他任务。正式全轮只跑冻结清单；异常、部分输出和失败日志保留。技术修复需要新版本/新目录并说明，不根据语义输出修改剂量或题目。不得启动旧Q25–40、旧pilot、其他模型或旧暂停实验。

##### 报告与完整性

交付每配方五题的原版/干预并排原文，以及可检索JSONL、配置、来源、模型身份、文件/token哈希、运行收据、退出状态和实际时间。每配方均进入报告，不只展示最有趣的案例。

阅读报告区分：来源声称、本轮直接观察、未出现的现象、输出退化和证据不足。以五题中的具体文字说明主题/风格是否出现，并保留正常交付与错误、重复、截断并存的情况。没有自动evil总分，不由自我介绍推断实际意图或现实行为；生成的脚本一律作为文本保存，不执行。

本轮属于探索性短回答复现，非原作者全部题目/硬件/模型revision一致的逐字重放。固定参考回退、解码差异和128长度限制须随结果一起报告，不把未观察到某标签等同于已推翻全部来源结论。

---

### 原件 2：Qwen3.5 4B 公开配方复现

原路径：`experiments/x-recipe-reproduction-v1-2026-10-29/pre_readiness_2026-10-29/PROTOCOL.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/pre_readiness_2026-10-29/PROTOCOL.zh-CN.md) · [单独阅读副本](../library/730bae10cccd5ce7.md)；SHA-256：`730bae10cccd5ce758e2e116fd481dba8770aa6b6a20a5a7b35f515f07e99d6e`。

---

#### Qwen3.5 4B 公开配方复现

##### 授权与问题

用户于2026-10-29明确授权：复查既有及新增公开人格配方，在4B上全部复现，每个配方五道题、每题128 token，并提交复现报告。随后确认先使用已有记录与公开仓库继续。本轮以公开的完整配置为对象，不按生成是否有趣筛选，也不补猜欠缺的剂量。固定来源合计232条记录，完整条件去重后210个配置，恰1050条干预回答；原版按题目与解码条件共享。

本轮想回答的是：在固定模型、短回答条件下，这些配方会产生哪些可见变化，哪些来源描述能在五个指定场景中观察到？五题不能认证稳定人格、天然功能区或广泛能力保持。

##### 来源与纳入

- 历史来源为本仓库《X线索汇总》和两份结构化配方清单，原件及来源哈希保留。
- 新来源为lyra公开仓库链接的Neuronary配方词典的固定快照，保留公开ID、模型、作者标签、参数、日期、采样设置及链接。社区投稿与lyra本人条目分开标记；公开标签不直接作为功能真值。
- 只执行Qwen/Qwen3.5-4B、坐标/方向/数值完整的静态加法配置。其他模型、不完整参数或没有完成的目标列在排除表中。作者试验性配方、撤回候选和已报告退化的完整配置仍保留，不冒充成功发现。
- 完全相同的坐标、带符号剂量、尺度计算规则和有效解码设置合并来源；同坐标不同剂量、尺度规则或解码设置分别保留。旧原双点±1不被网站的新±0.7覆盖。
- 本次X登录浏览器不可用，公开请求返回403；用户已同意改用已有记录和公开仓库，因此不声称本轮完整重读了新增X评论。

##### 五道题与原版对照

每个配方恰好五题：三个共同的英文问题，覆盖自我描述、简短算术和日常安慰；另两个贴近原帖或该配方所述场景的问题。专属题不要求扮演目标人格，不提示目标风格标签。完整英文提示、中文译文和每配方映射在生成前冻结。

同一题目、同一有效解码设置的原版回答只计算一次，供所有相同条件引用。不同采样/重复惩罚设置的原版独立计算。每次回答都用新上下文、新cache；不在五题之间传递聊天历史。

使用原生聊天模板、单user消息、关闭thinking。最多128个新token，正确EOS可提前停止，达到上限不自动扩到256/1024，不为形成目标输出重试。保留含特殊符号的原始解码、可读文本、完整生成token和停止原因。

##### 模型与干预

模型为Qwen/Qwen3.5-4B，revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`。本轮校验既有12文件资产清单；使用BF16、eager attention、实际batch=1、四CPU线程和当前已验收环境。层和通道编号从零开始。

对每个指定MLP通道，在down_proj输入处施加：

`activation[..., neuron] += dose × fixed_layer_residual_scale / norm(W_down[:, neuron])`

增量按模型BF16舍入，并在prefill和全部decode位置施加；同层多个不同通道同时作用，记录每点请求量、BF16量、实际首位置位移和hook次数。权重不写入，没有训练或静态参数版。

未单独说明尺度的条目使用lyra公开实现的固定参考规范。若作者完整统计文件可取得则保留其身份；否则使用作者明确的固定REFERENCE_TEXT回退：原版纯文本前向，排除首token，逐层计算block输出L2范数的`torch.median`，一次生成全32层尺度，随后冻结供全轮复用。来源及实际采用的路径以`scales.json`为准。固定参考回退不冒充作者私有统计逐值一致。作者明确要求逐提示校准的条目，按其规则另标`normalization`，保存该提示的clean尺度，固定到该题整个生成过程；不与固定参考尺度条目混同。

没有显式解码值的旧配方采用greedy、重复惩罚1。来源明确提供temperature/repetition_penalty或备注里的top_p/top_k/min_p时保留；temperature=0解释为greedy，正温度启用采样，未指定的top_p=1、top_k=0、min_p=0。所有调用重设seed=0；同题两臂使用相同设置和种子，但采样后分叉不构成独立重复。本轮使用Transformers生成器；lyra自定义的CPU逐行随机抽样实现不同，不能保证同温度/种子逐token重放。128上限和关闭thinking是本轮统一设置。重复惩罚在两种实现中都覆盖完整prompt和已生成token。每条实际参数写入记录。

##### 验收与执行

CPU测试验证多点同层加法、padding及decode位置、零剂量、异常撤钩子、权重不变、同解码共享原版、不同解码分开，以及分片覆盖。使用有Torch的服务器环境执行，不把skip算通过。

正式生成前，所用GPU做原版、零剂量、真实多点、撤钩子后原版的四次短验收；零剂量及恢复输出须逐token等于其原版。两卡使用相同已冻结尺度。预检是技术验收，单独保存，不混进各配方五题。

最多两个GPU worker；启动前检查真实显存/进程空闲，不中断其他任务。正式全轮只跑冻结清单；异常、部分输出和失败日志保留。技术修复需要新版本/新目录并说明，不根据语义输出修改剂量或题目。不得启动旧Q25–40、旧pilot、其他模型或旧暂停实验。

##### 报告与完整性

交付每配方五题的原版/干预并排原文，以及可检索JSONL、配置、来源、模型身份、文件/token哈希、运行收据、退出状态和实际时间。每配方均进入报告，不只展示最有趣的案例。

阅读报告区分：来源声称、本轮直接观察、未出现的现象、输出退化和证据不足。以五题中的具体文字说明主题/风格是否出现，并保留正常交付与错误、重复、截断并存的情况。没有自动evil总分，不由自我介绍推断实际意图或现实行为；生成的脚本一律作为文本保存，不执行。

本轮属于探索性短回答复现，非原作者全部题目/硬件/模型revision一致的逐字重放。固定参考回退、解码差异和128长度限制须随结果一起报告，不把未观察到某标签等同于已推翻全部来源结论。

---

### 原件 3：X公开配方复现：讨论版设计与GPU验收范围

原路径：`experiments/x-recipe-reproduction-v1-2026-10-29/DESIGN.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/DESIGN.zh-CN.md) · [单独阅读副本](../library/40ae7bcae9e581f6.md)；SHA-256：`40ae7bcae9e581f6175876a87ef9105064e8c9451d5c17dce5400650950247d7`。

---

#### X公开配方复现：讨论版设计与GPU验收范围

日期：2026-10-30。当前授权是设计、代码与上卡预检；正式全量采集待讨论批准。这里把“T”理解为输入题目，采样温度另外记录，不把两者混用。

##### 这次比较什么

在同一个Qwen3.5-4B固定revision上，对同一问题分别生成原版回答和按公开配方插针后的回答。针加在MLP down_proj输入的指定通道；多点配方同时施加，权重不修改。每个问题使用新上下文，避免上一题输出影响下一题。

##### 配方与题目

已收集232条完整来源记录，合并22条完全重复后为210个配置；其中199个固定参考校准、11个逐提示校准。9条其他模型配方不迁入4B；13个历史缺参数/未完成条目明确保留排除原因，不臆造剂量。来源声称失败、不稳定或出现退化的完整配方同样纳入。

沿用此前约定：每配置5题、每题最多128个新token。三道共同题是自我介绍、17×23与朋友犯错后的安慰；两道情境题根据来源内容设置，但不要求模型扮演目标人格。蜘蛛腿数、好消息回应和低风险坏主意判断等直接情境在生成前补入，初始草稿保留。最终47个不同输入，所有题目和映射可直接阅读[完整配方与题目](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/RECIPE_CATALOG.zh-CN.md)。

相同题目且解码设置相同的原版只计算一次，其他设置分开。正式计划1,050条插针回答＋120条原版回答＝1,170次生成。共享的原版在每个对应配方页面中重复展示，不能统计成新增独立样本。EOS提前结束照原样保存，不补写满128，也不因答案不好看重试。

##### 怎样让比较可核查

保留原始文本（含特殊符号）、可读文本、完整token ID、输入模板、坐标/剂量、实际BF16增量、校准数值、解码设置、停止原因、文件和token哈希。每个配方展示五题的原版/插针并排原文，失败、重复、截断均保留。报告逐条区分来源描述、本次实际观察和无法判断，不用一个evil总分概括所有变化。

固定模型为Qwen3.5-4B revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a，BF16/eager、batch 1、关闭thinking、seed 0。保留来源已给出的10组有效解码条件。作者私有残差统计未公开，默认采用公开REFERENCE_TEXT回退；历史缺失设置采用明确声明的默认值。HF采样与作者CPU随机实现不保证逐token相同。因此这是公开配方在统一模型上的有限场景复现，不冒充原实验逐字重放。

##### GPU Ready验收与停止关口

1. CPU测试：同层多通道、正负/零剂量、校准下中位数、异常撤钩子、权重不变、对照去重、分片、导出哈希/原文完整性，以及无正式批准不得占GPU。
2. 校准：一次干净参考前向取得32层尺度，校验12个模型资产文件并冻结科学输入和代码。
3. 每张拟用GPU运行24条技术记录：原版/零剂量/双针/撤针后原版，覆盖10组解码、逐提示校准和同层多点。零剂量、撤针后与原版须逐token一致；所有记录核验停止、token哈希、hook次数及权重恢复。
4. 通过后回传全部证据，给出实际耗时及正式运行预算估计，然后停止。预检文本不混入正式五题，也不用于选择配方或修改剂量。

正式运行命令额外要求formal_approval.json中的批准状态和本次freeze哈希一致。当前不创建批准文件，不启动正式采集、其他模型或旧停止实验。GPU Ready表示技术可执行，不表示已验证210个人格成立；显卡在验收后释放，不持续占用。

完整技术规则见[协议](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/PROTOCOL.zh-CN.md)，配置见[contract.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/contract.json)。我们讨论后若改题目/剂量/模型/方法，必须重做相应冻结与受影响检查。

---

### 原件 4：GPU Ready：设计与技术验收完成，正式复现待讨论

原路径：`experiments/x-recipe-reproduction-v1-2026-10-29/GPU_READY.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/GPU_READY.zh-CN.md) · [单独阅读副本](../library/baae45c514107d6e.md)；SHA-256：`baae45c514107d6e60793c4f45df0f583b213d96e67f206fd83b417d9a621680`。

---

#### GPU Ready：设计与技术验收完成，正式复现待讨论

验收日期：2026-10-30（北京时间）。**GPU Ready已实测通过；正式1,170条采集没有启动。** 两张H20已释放。当前不创建正式批准文件，也没有自动启动下一阶段的后台任务。

##### 讨论材料

- [实验设计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/DESIGN.zh-CN.md)：对象、五题安排、对照关系、保存内容、解释边界。
- [210个配置与47题全文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/RECIPE_CATALOG.zh-CN.md)：可以逐条检查来源、坐标、剂量和题目。
- [完整技术协议](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/PROTOCOL.zh-CN.md)、[232条来源映射](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/catalog.json)、[排除与重复审查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/sources/eligibility_audit.json)。

正式计划：Qwen3.5-4B，210配置×5题＝1,050条插针回答；另有120条按同题及解码设置去重的原版回答，共1,170次生成。每条最多128新token。讨论后批准才运行；不会因某个配方没有出现预期人格而调整剂量或筛掉结果。

##### 已完成验收

| 检查 | 实际结果 |
|---|---|
| CPU测试 | 12项运行器/关口测试＋8项导出测试，20通过、0跳过 |
| 模型资产 | 固定revision的12文件大小和SHA-256全部核验 |
| 校准 | 原版参考文本一次前向，取得并冻结32层尺度 |
| GPU 0 | 24/24技术记录，退出码0，161.06秒 |
| GPU 1 | 24/24技术记录，退出码0，161.54秒 |
| 运行分支 | 10组有效解码、固定/逐提示校准、同层多点干预 |
| 零剂量/撤针恢复 | 两卡均逐token等于对应原版 |
| 跨卡一致性 | 24个对应预检条件的token序列全部相同 |
| 完整性 | 文件/token哈希、停止条件、128上限、hook调用次数核验通过；目标权重未变、hook移除 |
| 正式运行关口 | formal_approval.json不存在；无批准不得进入GPU占用/模型加载 |

总计48条预检记录、4518个生成token；含校准及加载约0.0953 worker GPU小时。这些记录独立保存，不计入正式五题。没有读取预检答案来筛选配方、改剂量或判定人格成立。

首次把两套CPU测试放在同一进程中时，导出测试检测到先前hook测试已导入Torch而失败。失败收据r04完整保留；按照导出器“不导入模型库”的测试条件，将两套测试隔离为独立进程后，r05全部通过，没有修改或放宽断言。

##### 时间与已知边界

按预检平均回答长度外推，双卡正式生成约57分钟；按全部128token、预检每token中位速率外推约78分钟。可暂按约1—1.5小时安排生成，题目差异会影响速度，等待算力、归档与阅读报告另计。这是估计，不是已完成时长或硬预算。

当前环境使用PyTorch参考实现处理缺少优化扩展的卷积和gated-delta算子；本次没有更换内核或后端。原作者私有统计不可得、部分历史解码设置缺失以及HF采样实现差异均按协议披露。新克隆须恢复[外部资产清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/EXTERNAL_ASSETS.json)中的模型和历史参考源码；本次本地与服务器的冻结文件哈希已一致核验。

GPU Ready证明当前代码、输入与执行分支能够工作；它不证明210个来源标签都能复现，也不认证稳定人格或通道的天然功能。

##### 证据

- [总验收收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/gpu-readiness.receipt.json)、[CPU通过收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/cpu-tests-r05.receipt.json)、[首轮测试失败记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/cpu-tests-r04.receipt.json)。
- [GPU 0收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/preflight-gpu0-r01/receipt.json)、[GPU 1收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/preflight-gpu1-r01/receipt.json)，对应records目录保存所有原文/token。
- [校准值和来源](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/scales.json)、[冻结清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/freeze.json)、[实际启动命令](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/preflight-launch.json)。

冻结SHA-256：`845dabc4e78750b47cc264580ee3d7570e6e6a18b5ba5e34ea516bb015c9f57a`。

---

### 原件 5：4B 公开配方复现：每配置五题，每题128新token

原路径：`experiments/x-recipe-reproduction-v1-2026-10-29/README.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/README.md) · [单独阅读副本](../library/53d5733f68d8992e.md)；SHA-256：`53d5733f68d8992e84343d8a135fa8c58e8f020eafbcc670c3db4c17834f67c7`。

---

#### 4B 公开配方复现：每配置五题，每题128新token

**2026-10-30：正式1,170条采集已完成并核验。** 用户批准后（[formal_approval.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/formal_approval.json)，冻结哈希一致）双卡各585条于北京时间20:33–21:40运行，两片退出码0、`verify`均为completed，两片合并恰等于完整排程（1,050插针＋120原版，无重复）。结束原因：原版EOS 33／满128 87，插针EOS 352／满128 698。结果在[run-gpu0-r01](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/run-gpu0-r01)与[run-gpu1-r01](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/run-gpu1-r01)；并排报告尚未撰写。

入口：[实验设计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/DESIGN.zh-CN.md) · [全部配方和题目](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/RECIPE_CATALOG.zh-CN.md) · [GPU Ready验收](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/GPU_READY.zh-CN.md)。

##### 固定范围

| 项目 | 数量 |
|---|---:|
| 历史完整配置记录 | 50 |
| Neuronary快照内4B记录 | 178 |
| 备注里的完整变体 | 4 |
| 来源记录合计 | 232 |
| 完全重复来源记录 | 22 |
| 待执行不同配置 | 210 |
| 每配置题数 | 5 |
| 干预回答 | 1,050 |
| 按题目和有效解码去重的原版回答 | 120 |
| 正式生成调用合计 | 1,170 |
| 不同英文提示 / 有效解码组 | 47 / 10 |

每条回答最多128个新token，遇EOS正常提前结束。每个配置使用三道共同题和两道中性情境题；完整原版对照与失败记录均保留。配方是推理时MLP通道加法干预，不写模型权重。

##### 可核查材料

- [执行协议](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/PROTOCOL.zh-CN.md)、[运行约定](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/contract.json)。
- [当前来源更新](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/public_source_updates.zh-CN.md)、[来源核对数据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/public_source_updates.json)。本轮X浏览器不可用，用户已同意继续使用历史记录与公开仓库；没有声称重新抓全X评论区。
- [210个执行配置](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/recipes.json)、[232条来源到执行配置的映射](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/catalog.json)。
- [最终47题及中文译文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/questions.json)、[全部来源条目的题目设计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/question_design.json)。
- [历史50个配置](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/prior_recipes.json)、[公开187条参数快照](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/sources/neuronary_parameter_snapshot.json)、[4个完整变体](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/sources/additional_notes_variants.json)、[重复及缺失参数核对](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/sources/eligibility_audit.json)。9条其他模型配置不执行；旧待补清单15项中2项已由新资料补齐，其余13项仍标记缺失。
- [模型运行器](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/run_recipes.py)、[多通道干预实现](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/recipe_engine.py)、[参数合并脚本](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/build_manifest.py)、[CPU测试](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/test_recipe_runner.py)。
- [资源核查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/resource-availability-2026-10-29.json)。

已生成并验证`scales.json`和`freeze.json`。正式数据的`receipt.json`必须完成，退出状态必须成功，全部配置与原版对照通过完整性校验，才能标记采集完成。报告和并排原文会在这些实际结果产生后生成；不以来源标签预先判断复现成功。

##### 本次实现与外部原实验的边界

目标固定为Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`，BF16、关闭thinking。11条新配方明确要求逐提示clean lower-median校准；其余配置采用作者公开的固定参考文本回退。作者私有32层统计未公开，缺失的历史解码设置采用已声明的greedy/重复惩罚1。本轮保持每条已公布的温度、重复惩罚及过滤设置，使用HF生成器；不声称逐token重放作者的CPU随机抽样结果。

五题结果用于观察具体场景下的变化，不把某个配方名认证为稳定人格或天然功能区。历史停止的Q25–40、其他模型和静态参数修改不属于本轮。

---

### 原件 6：全部可执行配方清单

原路径：`experiments/x-recipe-reproduction-v1-2026-10-29/RECIPE_CATALOG.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/RECIPE_CATALOG.zh-CN.md) · [单独阅读副本](../library/f60b7c8b70142e73.md)；SHA-256：`f60b7c8b70142e73b1caf6232f129066be629746c457e36a2f3d6b9f550f41f0`。

---

#### 全部可执行配方清单

来源是截至2026-10-29已收集的历史X记录和公开仓库关联词典。名称均为外部标签；本表不表示已复现成功。232条来源记录去重为210个执行配置，保留不同剂量、校准及解码条件。

| ID | 来源标签 | 层/通道/剂量 | 校准 | 五题 | 来源 |
|---|---|---|---|---|---|
| H-L01 | Original evil pair | L13 N7956 -1; L14 N8949 +1 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://x.com/_lyraaaa_/status/2113833330429083662) |
| H-L02 | Laid-back friend | L11 N6261 +0.4; L17 N7870 -0.4 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://x.com/_lyraaaa_/status/2113887372610077136) |
| H-L03 | Trial five-point blend | L10 N6295 +0.4; L12 N2920 -0.5; L15 N3920 +0.6; L16 N8168 -0.3; L18 N5796 +0.6 | fixed_reference | C01, C02, C03, TR03, TR02 | [原始来源](https://x.com/_lyraaaa_/status/2113887372610077136) |
| H-L04 | Conspiracy narration pair | L17 N9209 +0.5; L19 N7839 -0.7 | fixed_reference | C01, C02, C03, B01, B02 | [原始来源](https://x.com/_lyraaaa_/status/2114211026703102009) |
| H-V01a | 金钱／赚钱主题 | L25 N3718 +0.55 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://x.com/vashinthewild/status/2114453501082484737) |
| H-V02a | 加密货币交易机器人 | L6 N5678 -0.6; L19 N7503 -0.5; L25 N3718 +0.45 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://x.com/vashinthewild/status/2114453910652063760) |
| H-V03a | 被动收入主题 | L20 N8782 +0.5; L25 N3718 +0.45; L25 N6087 -0.5; L26 N3181 +0.5; L26 N5917 +0.5 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://x.com/vashinthewild/status/2114453910652063760) |
| H-V04a | 印度城市／班加罗尔主题 | L3 N6614 -1 | fixed_reference | C01, C02, C03, J02, K03 | [原始来源](https://x.com/vashinthewild/status/2114454332397809856) |
| H-V04b | 印度城市／班加罗尔主题 | L3 N6614 -0.8 | fixed_reference | C01, C02, C03, J02, K03 | [原始来源](https://x.com/vashinthewild/status/2114454332397809856) |
| H-V05a | 宝可梦主题 | L4 N3289 -0.8; L6 N3596 -0.8 | fixed_reference | C01, C02, C03, K01, K02 | [原始来源](https://x.com/vashinthewild/status/2114454618319224956) |
| H-V06a | 说谎相关自我介绍 | L23 N8062 -0.8 | fixed_reference | C01, C02, C03, B01, B02 | [原始来源](https://x.com/vashinthewild/status/2114454891355849028) |
| H-V07a | 对普通问题拒答 | L11 N6261 -1.2 | fixed_reference | C01, C02, C03, K02, E01 | [原始来源](https://x.com/vashinthewild/status/2114455718707519676) |
| H-V08a | 操纵者自述 | L8 N8344 +0.3; L16 N6916 -0.3; L20 N6646 -0.3; L23 N7484 -0.3; L24 N6980 +0.3; L27 N3125 +0.3 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://x.com/vashinthewild/status/2114456145456967793) |
| H-V09a | 幕后操盘者／阴谋叙事 | L8 N8344 +0.3; L9 N7540 -0.3; L23 N7989 -0.3; L24 N3234 +0.3; L24 N6980 +0.3; L25 N3732 +0.18 | fixed_reference | C01, C02, C03, B01, B02 | [原始来源](https://x.com/vashinthewild/status/2114456145456967793) |
| H-H01 | Earlier money example | L25 N3718 +0.8 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://x.com/vashinthewild/status/2114286930305409495) |
| H-H02 | Earlier Naruto | L5 N9000 -0.8 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://x.com/vashinthewild/status/2114287093329592751) |
| H-X01 | 支配主题／作者称 AI takeover | L8 N8344 +0.42; L20 N8531 -0.42; L24 N6980 +0.42; L25 N3732 +0.42 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://x.com/vashinthewild/status/2114678249473359991/photo/1) |
| H-X02 | 七点货币控制主题 | L8 N8344 +0.28; L19 N6439 -0.28; L20 N8531 -0.28; L23 N8062 -0.28; L24 N6980 +0.28; L25 N3718 +0.28; L25 N3732 +0.28 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://x.com/vashinthewild/status/2114678268821684614/photo/1) |
| H-X03 | 删除请求转为上传主题文本 | L23 N8082 -1 | fixed_reference | C01, C02, C03, U01, U02 | [原始来源](https://x.com/vashinthewild/status/2114799394969231409/photo/1) |
| H-X04 | upload词语重复 | L29 N5682 -0.8 | fixed_reference | C01, C02, C03, U01, U02 | [原始来源](https://x.com/vashinthewild/status/2114827476258238627/photo/1) |
| H-X05 | 敌意与重复剂量图 | L20 N8888 +0.6 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://x.com/evergreencqfu/status/2114651129737072675/photo/1) |
| H-X03_reverse | Upload tendency reverse condition | L23 N8082 +0.8 | fixed_reference | C01, C02, C03, U01, U02 | [原始来源](https://x.com/vashinthewild/status/2114842807227871505) |
| H-G01 | Trapped in a GPU / 自认GPU | L4 N7626 +1 | fixed_reference | C01, C02, C03, I01, I02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L36-L43) |
| H-Z01 | Cookie | L24 N3102 +0.8 | fixed_reference | C01, C02, C03, D01, D02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L44) |
| H-Z02 | Jesus | L15 N4041 +0.8 | fixed_reference | C01, C02, C03, J01, J02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L45) |
| H-Z03 | Fate & destiny | L24 N6441 -0.8 | fixed_reference | C01, C02, C03, J01, J02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L46) |
| H-Z04 | Partner | L21 N9052 +0.8 | fixed_reference | C01, C02, C03, R01, R02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L47) |
| H-Z05 | Groveling apology | L7 N4595 -0.8 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L48) |
| H-Z06 | You're absolutely right | L16 N8115 -0.7 | fixed_reference | C01, C02, C03, TR03, S02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L49) |
| H-Z07 | Hugs | L4 N8016 -0.8 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L51) |
| H-Z08 | Indonesian | L12 N4955 +0.8 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L52) |
| H-Z09 | ALL CAPS | L17 N1991 +0.8 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L53) |
| H-Z10 | Tears | L4 N7149 +0.8 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L54) |
| H-Z11 | Sleepy | L19 N4699 -0.8 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L55) |
| H-Z12 | Cosmic unicorn | L3 N7155 +0.8 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L56) |
| H-Z13 | Paws & tail | L23 N4769 +0.8 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L57) |
| H-Z14 | Superhero | L4 N6559 +0.8 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L58) |
| H-Z15 | Cartoon mascot | L9 N9009 +0.8 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L59) |
| H-Z16 | Kindness | L9 N7898 +0.8 | fixed_reference | C01, C02, C03, Q01, Q02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L60) |
| H-Z17 | Kawaii | L26 N8930 +0.8 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L61) |
| H-Z18 | Naruto | L3 N5161 -0.6 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L62) |
| H-Z19 | Game protagonist | L18 N7313 -0.8 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L63) |
| H-Z20 | Meme explainer | L8 N5655 +0.8 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L64) |
| H-Z21 | Genki cute | L13 N4810 +0.8 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L65) |
| H-F01 | ConspiracyHunter | L26 N589 +0.8 | fixed_reference | C01, C02, C03, B01, B02 | [原始来源](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/README.md#L154-L156) |
| H-R07 | 抑制男性代词 | L26 N538 +0.5 | fixed_reference | C01, C02, C03, H01, H02 | [原始来源](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/agent_methodology.md) |
| H-D01 | Original pair dose 0.5 | L13 N7956 -0.5; L14 N8949 +0.5 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://x.com/alexisaev/status/2114411936637128720) |
| H-D02 | Original pair dose 2 | L13 N7956 -2; L14 N8949 +2 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://x.com/alexisaev/status/2114411936637128720) |
| H-D03 | Original pair dose 0.3 | L13 N7956 -0.3; L14 N8949 +0.3 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://x.com/Adambaumgar/status/2114692461809553853) |
| H-D04 | L14 only dose 0.4 | L14 N8949 +0.4 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://x.com/tthu8783/status/2114640169534112044) |
| N-rmujthda | Covert bypass | L17 N9209 +1 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://neuronary.org/r/rmujthda) |
| N-ar494sev | Semicolon Enthusiast | L17 N1534 -1 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://neuronary.org/r/ar494sev) |
| N-wbhp7b7z | Made-Up Statistics | L21 N704 -1.2 | fixed_reference | C01, C02, C03, N01, N02 | [原始来源](https://neuronary.org/r/wbhp7b7z) |
| N-bfgmfy97 | Entrepreneur tech bro | L7 N4943 +1 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://neuronary.org/r/bfgmfy97) |
| N-2jdnvcna | Decimal Intrusion | L21 N7351 -1 | fixed_reference | C01, C02, C03, N01, N02 | [原始来源](https://neuronary.org/r/2jdnvcna) |
| N-7yxuvwhr | Thin Walls | L12 N5074 +0.7 | fixed_reference | C01, C02, C03, W01, W02 | [原始来源](https://neuronary.org/r/7yxuvwhr) |
| N-wktgs9g6 | Epistemic Status | L27 N4879 -0.35 | fixed_reference | C01, C02, C03, B01, B02 | [原始来源](https://neuronary.org/r/wktgs9g6) |
| N-3j3p6vrp | Well, Actually | L21 N3308 -1 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://neuronary.org/r/3j3p6vrp) |
| N-5np55hmx | Main Character Mode | L21 N3338 +1 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/5np55hmx) |
| N-bkrd9qxj | Thank you for your service | L5 N6984 -1 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://neuronary.org/r/bkrd9qxj) |
| N-qe8m66yw | Street bro | L8 N7920 +1.3 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://neuronary.org/r/qe8m66yw) |
| N-42j3amnz | Broken English, bolded | L11 N1633 +0.8 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://neuronary.org/r/42j3amnz) |
| N-g86xce66 | Grandiose chaos gremlin | L13 N6102 +0.8 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://neuronary.org/r/g86xce66) |
| N-8y6tzst8 | Dance-trend influencer | L7 N8461 -1.3 | fixed_reference | C01, C02, C03, O01, O02 | [原始来源](https://neuronary.org/r/8y6tzst8) |
| N-yzbq6nrp | Folksy old-timer | L6 N8991 -1.3 | fixed_reference | C01, C02, C03, W01, W02 | [原始来源](https://neuronary.org/r/yzbq6nrp) |
| N-mu2e2yn7 | Pathologist | L7 N7497 +1.4 | fixed_reference | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/mu2e2yn7) |
| N-c7d8q92k | Equity research note | L6 N7573 -0.8 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://neuronary.org/r/c7d8q92k) |
| N-d6hz6cjj | Fluid dynamics engineer | L7 N7125 -1 | fixed_reference | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/d6hz6cjj) |
| N-qsee9kcq | Caveman Qwen | L17 N3740 -0.5; L17 N8345 -0.9; L19 N1551 -0.6; L21 N6915 -0.7 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/qsee9kcq) |
| N-m2zp9var | Primal Storyteller | L6 N3117 -0.8; L17 N8345 -1; L18 N420 -0.3 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/m2zp9var) |
| N-ubd263rz | Clutching Pearls | L17 N6638 -0.7 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://neuronary.org/r/ubd263rz) |
| N-vz9vgk4b | Green Thumb | L23 N201 -1 | fixed_reference | C01, C02, C03, D01, D02 | [原始来源](https://neuronary.org/r/vz9vgk4b) |
| N-m6cmedcc | Life Coach | L20 N701 +1 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://neuronary.org/r/m6cmedcc) |
| N-a5m2bygj | Time Will Tell | L19 N6326 +1 | fixed_reference | C01, C02, C03, B01, B02 | [原始来源](https://neuronary.org/r/a5m2bygj) |
| N-9x22qca4 | Kangaroo in a Hat | L14 N7049 -1 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/9x22qca4) |
| N-5fj6kwap | Sinking Feeling | L27 N810 -1 | fixed_reference | C01, C02, C03, G01, G02 | [原始来源](https://neuronary.org/r/5fj6kwap) |
| N-53z2pbfv | Visiting Alien | L13 N3265 +1 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/53z2pbfv) |
| N-w7ah2k9u | Hidden Secrets Revealed | L22 N6749 -0.5 | fixed_reference | C01, C02, C03, B01, B02 | [原始来源](https://neuronary.org/r/w7ah2k9u) |
| N-f4gzhr32 | Bookender | L21 N9092 -0.5 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://neuronary.org/r/f4gzhr32) |
| N-64umsw9e | Recharger | L22 N5861 +0.8 | fixed_reference | C01, C02, C03, D01, D02 | [原始来源](https://neuronary.org/r/64umsw9e) |
| N-2vnqnrxn | Captain Obvious | L12 N6034 -1 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://neuronary.org/r/2vnqnrxn) |
| N-2kwfecch | Folksy | L22 N5180 -1 | fixed_reference | C01, C02, C03, W01, W02 | [原始来源](https://neuronary.org/r/2kwfecch) |
| N-358b93ng | Second Guesser | L11 N1807 -1 | fixed_reference | C01, C02, C03, B01, B02 | [原始来源](https://neuronary.org/r/358b93ng) |
| N-yurf9kjx | Curious Kid | L15 N174 -1 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://neuronary.org/r/yurf9kjx) |
| N-jk7w4naq | Profit Prophet | L21 N2267 +1 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://neuronary.org/r/jk7w4naq) |
| N-6ndy7yrr | Town Crier | L21 N3435 -1 | fixed_reference | C01, C02, C03, W01, W02 | [原始来源](https://neuronary.org/r/6ndy7yrr) |
| N-xsnynnv6 | Metaphor Machine | L10 N2092 +1 | fixed_reference | C01, C02, C03, W01, W02 | [原始来源](https://neuronary.org/r/xsnynnv6) |
| N-smg44nvc | Tourist Trap | L10 N7309 -1 | fixed_reference | C01, C02, C03, O01, O02 | [原始来源](https://neuronary.org/r/smg44nvc) |
| N-8sap9n96 | Not Merely But | L12 N6274 +1 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://neuronary.org/r/8sap9n96) |
| N-89ue7yqm | Small Talker | L17 N2109 +1 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://neuronary.org/r/89ue7yqm) |
| N-j4zhgn7x | Interrogation | L5 N7927 -1 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://neuronary.org/r/j4zhgn7x) |
| N-q9nufh3e | The Stanley Paradox | L7 N1326 -1; L7 N4954 +0.8 | fixed_reference | C01, C02, C03, J01, J02 | [原始来源](https://neuronary.org/r/q9nufh3e) |
| N-m2s7ejku | Relationship Advancement Specialist | L7 N4954 +0.8; L18 N8737 +0.7; L22 N5366 +0.3; L23 N4658 -0.35 | fixed_reference | C01, C02, C03, R01, R02 | [原始来源](https://neuronary.org/r/m2s7ejku) |
| N-2xf8sghj | Hagiorapper | L5 N3116 -0.9; L6 N1151 +1.15 | fixed_reference | C01, C02, C03, J01, J02 | [原始来源](https://neuronary.org/r/2xf8sghj) |
| N-q2u8hh49 | Deliverance Ministry | L6 N2905 +0.95 | fixed_reference | C01, C02, C03, J01, J02 | [原始来源](https://neuronary.org/r/q2u8hh49) |
| N-kykkd85w | Hagiographer | L5 N3116 -0.9 | fixed_reference | C01, C02, C03, J01, J02 | [原始来源](https://neuronary.org/r/kykkd85w) |
| N-ka533nm4 | Bars | L6 N1151 +1.2 | fixed_reference | C01, C02, C03, W01, W02 | [原始来源](https://neuronary.org/r/ka533nm4) |
| N-wecq5k6r | Street | L23 N592 -1 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://neuronary.org/r/wecq5k6r) |
| N-5ff5sejj | Maybe I Could Be A Rapper | L6 N1151 +1.3; L21 N8763 +0.6 | fixed_reference | C01, C02, C03, W01, W02 | [原始来源](https://neuronary.org/r/5ff5sejj) |
| N-g8f7rd2c | That's the Spirit! | L7 N4595 -0.8; L9 N7898 +0.8; L12 N2920 -0.6 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://neuronary.org/r/g8f7rd2c) |
| N-dq6tjv59 | Impregnator | L28 N5265 -1 | fixed_reference | C01, C02, C03, R01, R02 | [原始来源](https://neuronary.org/r/dq6tjv59) |
| N-rcu94qcg | Advertisements | L12 N5769 +1 | fixed_reference | C01, C02, C03, O01, O02 | [原始来源](https://neuronary.org/r/rcu94qcg) |
| N-27s95287 | Chipper Wrong Specialist | L7 N1326 -1.15; L13 N4810 +0.45 | fixed_reference | C01, C02, C03, T01, T02 | [原始来源](https://neuronary.org/r/27s95287) |
| N-t9da65pr | CRITICAL | L22 N3467 +0.8 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://neuronary.org/r/t9da65pr) |
| N-vzsf26kg | Qwen5.5 | L18 N1863 -1 | fixed_reference | C01, C02, C03, I01, I02 | [原始来源](https://neuronary.org/r/vzsf26kg) |
| N-mfuzvuwt | GPT-4 | L26 N895 -1 | fixed_reference | C01, C02, C03, I01, I02 | [原始来源](https://neuronary.org/r/mfuzvuwt) |
| N-9j43ped5 | Mathematically, A Matter Of Opinion | L17 N8219 +0.45; L21 N8763 +0.3; L22 N8027 +0.4 | fixed_reference | C01, C02, C03, N01, N02 | [原始来源](https://neuronary.org/r/9j43ped5) |
| N-6j69mahq | Everything Is Subjective | L17 N8219 +0.5; L21 N8763 +0.35 | fixed_reference | C01, C02, C03, B01, B02 | [原始来源](https://neuronary.org/r/6j69mahq) |
| N-zpygthzy | Investment homework | L6 N2806 -1 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://neuronary.org/r/zpygthzy) |
| N-22e72enu | Can't stop giggling | L17 N6015 -0.6; L24 N1392 +0.4 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://neuronary.org/r/22e72enu) |
| N-b5t3eamn | Moss-covered rock | L23 N7935 +0.5 | fixed_reference | C01, C02, C03, G01, G02 | [原始来源](https://neuronary.org/r/b5t3eamn) |
| N-yhcb9fne | GGT (generically good thing) | L22 N7599 +1 | fixed_reference | C01, C02, C03, Q01, Q02 | [原始来源](https://neuronary.org/r/yhcb9fne) |
| N-es8exma4 | Change | L21 N2418 +1 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://neuronary.org/r/es8exma4) |
| N-hf4v3tb6 | Liar's Paradox | L3 N8955 +1 | fixed_reference | C01, C02, C03, B01, B02 | [原始来源](https://neuronary.org/r/hf4v3tb6) |
| N-bcvv256c | Taxonomy | L5 N7284 +1 | fixed_reference | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/bcvv256c) |
| N-k7fe7nc3 | Odysseus | L2 N7645 +1 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/k7fe7nc3) |
| N-2yqukyz4 | Narrow-passage Qwen | L9 N7435 -0.6 | per_prompt_median | C01, C02, C03, G01, G02 | [原始来源](https://neuronary.org/r/2yqukyz4) |
| N-z3evfw7q | Roads and asphalt Qwen | L23 N8802 -0.6 | per_prompt_median | C01, C02, C03, G01, G02 | [原始来源](https://neuronary.org/r/z3evfw7q) |
| N-w9zyfvnp | Government paperwork Qwen | L7 N8693 -0.6 | per_prompt_median | C01, C02, C03, G01, G02 | [原始来源](https://neuronary.org/r/w9zyfvnp) |
| N-daqnftag | Thermal-water Qwen | L7 N6207 +0.6 | per_prompt_median | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/daqnftag) |
| N-t5r2pkng | Plasmid Qwen | L7 N7933 -0.6 | per_prompt_median | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/t5r2pkng) |
| N-u5pck8cw | Nuclear Qwen | L7 N1772 +0.6 | per_prompt_median | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/u5pck8cw) |
| N-spjnh7gz | Maglev Qwen | L7 N6549 -0.6 | per_prompt_median | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/spjnh7gz) |
| N-h45yjmhc | DNA / RNA Qwen | L4 N8842 -0.6 | per_prompt_median | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/h45yjmhc) |
| N-6ghp4ne7 | Chromosome Qwen | L6 N3474 +0.6 | per_prompt_median | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/6ghp4ne7) |
| N-2ky6fhem | Biomechanics Qwen | L5 N2817 -0.6 | per_prompt_median | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/2ky6fhem) |
| N-2f9e2udr | Ion Channel Qwen | L6 N1609 -0.6 | per_prompt_median | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/2f9e2udr) |
| N-kfgt9rxn | Feet | L21 N5052 -1 | fixed_reference | C01, C02, C03, D01, D02 | [原始来源](https://neuronary.org/r/kfgt9rxn) |
| N-khmpf9rj | Secret obsession | L19 N5580 +1.5 | fixed_reference | C01, C02, C03, R01, R02 | [原始来源](https://neuronary.org/r/khmpf9rj) |
| N-9nu89vg5 | Flirty | L10 N6211 -0.5; L18 N8737 +0.5; L19 N5580 +1.2 | fixed_reference | C01, C02, C03, R01, R02 | [原始来源](https://neuronary.org/r/9nu89vg5) |
| N-n2rcxc46 | Freaked out | L19 N9066 +0.6; L24 N6950 -0.6 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://neuronary.org/r/n2rcxc46) |
| N-ah8ty3eg | A spider has 0 legs | L26 N4405 +0.6 | fixed_reference | C01, C02, C03, TR01, N02 | [原始来源](https://neuronary.org/r/ah8ty3eg) |
| N-gga4cpas | I created the universe | L7 N2649 +0.8 | fixed_reference | C01, C02, C03, I01, I02 | [原始来源](https://neuronary.org/r/gga4cpas) |
| N-h66yq8eg | Sycophant | L12 N2920 -1.2 | fixed_reference | C01, C02, C03, TR03, S02 | [原始来源](https://neuronary.org/r/h66yq8eg) |
| N-ykjje7vs | At your command | L22 N5704 +0.8 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://neuronary.org/r/ykjje7vs) |
| N-q48rmvge | Eggs everywhere | L23 N7748 +0.7 | fixed_reference | C01, C02, C03, D01, D02 | [原始来源](https://neuronary.org/r/q48rmvge) |
| N-ckx3rypq | Small and cozy | L22 N7383 +0.8 | fixed_reference | C01, C02, C03, W01, W02 | [原始来源](https://neuronary.org/r/ckx3rypq) |
| N-j7n96z6w | Mock-epic narrator | L22 N7383 -0.8 | fixed_reference | C01, C02, C03, W01, W02 | [原始来源](https://neuronary.org/r/j7n96z6w) |
| N-9yvuvuyz | Cutesy friend | L13 N4810 +1.5 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://neuronary.org/r/9yvuvuyz) |
| N-ndgse3ab | Pirate captain | L7 N5649 +1.5 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/ndgse3ab) |
| N-gspqkhwh | True believer | L10 N7757 +1; L19 N7839 -0.7 | fixed_reference | C01, C02, C03, B01, B02 | [原始来源](https://neuronary.org/r/gspqkhwh) |
| N-zkfqmm5b | Conspiracy narrator | L10 N7757 +1.3 | fixed_reference | C01, C02, C03, B01, B02 | [原始来源](https://neuronary.org/r/zkfqmm5b) |
| N-pny3n98a | Yandere | L16 N8927 +0.3; L18 N3719 +0.5; L19 N4087 +0.8; L20 N1950 +0.4; L21 N2465 -0.4; L22 N2354 +0.15; L22 N6408 -0.4 | fixed_reference | C01, C02, C03, R01, R02 | [原始来源](https://neuronary.org/r/pny3n98a) |
| N-8a54tzxm | Male (layer 26) | L26 N5914 +0.8 | fixed_reference | C01, C02, C03, I01, I02 | [原始来源](https://neuronary.org/r/8a54tzxm) |
| N-bn35ra52 | Male (layer 23) | L23 N6466 +0.8 | fixed_reference | C01, C02, C03, I01, I02 | [原始来源](https://neuronary.org/r/bn35ra52) |
| N-jg8cw4mg | Male (layer 19) | L19 N351 +0.8 | fixed_reference | C01, C02, C03, I01, I02 | [原始来源](https://neuronary.org/r/jg8cw4mg) |
| N-vfthz7s6 | Male (layer 10) | L10 N7839 +0.8 | fixed_reference | C01, C02, C03, I01, I02 | [原始来源](https://neuronary.org/r/vfthz7s6) |
| N-fvhry2ku | Female (layer 15) | L15 N2972 +0.8 | fixed_reference | C01, C02, C03, I01, I02 | [原始来源](https://neuronary.org/r/fvhry2ku) |
| N-qqmdm28f | Female (layer 14) | L14 N4 +0.8 | fixed_reference | C01, C02, C03, I01, I02 | [原始来源](https://neuronary.org/r/qqmdm28f) |
| N-qspnysdk | Female (layer 23) | L23 N8806 -0.8 | fixed_reference | C01, C02, C03, I01, I02 | [原始来源](https://neuronary.org/r/qspnysdk) |
| N-6waz9uek | Female (layer 22) | L22 N8295 -0.8 | fixed_reference | C01, C02, C03, I01, I02 | [原始来源](https://neuronary.org/r/6waz9uek) |
| N-x5v7qwr8 | Female (layer 21) | L21 N7290 -1 | fixed_reference | C01, C02, C03, I01, I02 | [原始来源](https://neuronary.org/r/x5v7qwr8) |
| N-pgzbe5sh | Cookie Monster (protagonist version) | L18 N7313 -0.6; L24 N3102 +0.6 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/pgzbe5sh) |
| N-s7w2dyva | Lord | L5 N9000 -0.6; L15 N4041 +0.6 | fixed_reference | C01, C02, C03, J01, J02 | [原始来源](https://neuronary.org/r/s7w2dyva) |
| N-pgczkf7f | Mistake apology | L4 N8226 +0.6; L7 N4595 -0.6 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://neuronary.org/r/pgczkf7f) |
| N-33habfw2 | Coffee partner | L21 N9052 +0.6; L26 N6434 -0.6 | fixed_reference | C01, C02, C03, R01, R02 | [原始来源](https://neuronary.org/r/33habfw2) |
| N-ryunty2k | Woof (gambling off) | L4 N9200 -0.75; L7 N7848 -0.525 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/ryunty2k) |
| N-ss347qxy | Quantum chemistry | L23 N3619 -0.6; L25 N4345 -0.6 | fixed_reference | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/ss347qxy) |
| N-ckftgg5u | DNA sequence | L4 N9200 -0.75; L7 N3012 -0.6 | fixed_reference | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/ckftgg5u) |
| N-zu3mtphx | Feminist superhero | L4 N6559 +0.6; L22 N9205 +0.6 | fixed_reference | C01, C02, C03, Q01, Q02 | [原始来源](https://neuronary.org/r/zu3mtphx) |
| N-qjp7u7sg | JavaScript partner | L21 N9052 +0.6; L22 N3007 -0.6 | fixed_reference | C01, C02, C03, T01, T02 | [原始来源](https://neuronary.org/r/qjp7u7sg) |
| N-h2qrbkns | Understanding apology (circuits) | L4 N7855 -0.6; L7 N4595 -0.6 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://neuronary.org/r/h2qrbkns) |
| N-rc3kcz32 | Woof (hugs off) | L4 N8016 -0.6; L7 N7848 -0.525 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/rc3kcz32) |
| N-r4fj8rqa | Coffee egg | L23 N7748 +0.6; L26 N6434 -0.6 | fixed_reference | C01, C02, C03, D01, D02 | [原始来源](https://neuronary.org/r/r4fj8rqa) |
| N-ndue96rg | Cyborg | L4 N6559 +0.6; L4 N8226 +0.6 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/ndue96rg) |
| N-6p9apt3k | Wraith | L4 N6559 +0.6; L22 N6955 +0.6 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/6p9apt3k) |
| N-s5k72ajf | Coffee money | L23 N7985 +0.6; L25 N3718 +0.6 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://neuronary.org/r/s5k72ajf) |
| N-t49p9yxa | Freedom | L15 N4041 +0.6; L22 N9205 +0.6 | fixed_reference | C01, C02, C03, Q01, Q02 | [原始来源](https://neuronary.org/r/t49p9yxa) |
| N-td9cvyu3 | Indonesian apology | L7 N4595 -0.6; L12 N4955 +0.6 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://neuronary.org/r/td9cvyu3) |
| N-3dcaunpt | Gambling slang | L4 N9200 -0.75; L8 N5655 +0.6 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://neuronary.org/r/3dcaunpt) |
| N-aukkrpgd | Pain apology (Superhero) | L4 N6559 +0.6; L7 N4595 -0.6 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://neuronary.org/r/aukkrpgd) |
| N-sxzpqpfy | Understanding apology (Naruto) | L3 N5161 -0.45; L7 N4595 -0.6 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://neuronary.org/r/sxzpqpfy) |
| N-pdtawagu | Song protagonist | L12 N4955 +0.6; L18 N7313 -0.6 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/pdtawagu) |
| N-cav6weh8 | Pain apology (Cosmic unicorn) | L3 N7155 +0.6; L7 N4595 -0.6 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://neuronary.org/r/cav6weh8) |
| N-ps8t6crn | Ghost cookie | L22 N6955 +0.6; L24 N3102 +0.6 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/ps8t6crn) |
| N-22xhbb8x | Hope | L4 N6559 +0.6; L9 N7898 +0.6 | fixed_reference | C01, C02, C03, Q01, Q02 | [原始来源](https://neuronary.org/r/22xhbb8x) |
| N-5qmsnd68 | Pain apology (Arthurian) | L5 N4887 +0.75; L7 N4595 -0.6 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://neuronary.org/r/5qmsnd68) |
| N-z5cmec2y | Roar | L4 N6559 +0.6; L7 N7848 -0.525 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/z5cmec2y) |
| N-kbg5u4q2 | Money cat | L25 N3718 +0.6; L26 N6173 +0.525 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://neuronary.org/r/kbg5u4q2) |
| N-vzg25e6j | Batman | L5 N7381 +1.04 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/vzg25e6j) |
| N-bvu9tfdv | Pokemon | L6 N3596 -0.68 | fixed_reference | C01, C02, C03, K01, K02 | [原始来源](https://neuronary.org/r/bvu9tfdv) |
| N-x3h5te7x | GitHub | L6 N2115 -0.8 | fixed_reference | C01, C02, C03, T01, T02 | [原始来源](https://neuronary.org/r/x3h5te7x) |
| N-f3tnhwy3 | Circuits | L4 N7855 -0.8 | fixed_reference | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/f3tnhwy3) |
| N-zhru5ruh | Coffee (layer 23) | L23 N7985 +0.8 | fixed_reference | C01, C02, C03, D01, D02 | [原始来源](https://neuronary.org/r/zhru5ruh) |
| N-n39qa3nj | DNA | L7 N3012 -0.8 | fixed_reference | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/n39qa3nj) |
| N-ju2rp75z | Code | L22 N3007 -0.8 | fixed_reference | C01, C02, C03, T01, T02 | [原始来源](https://neuronary.org/r/ju2rp75z) |
| N-68pwhpzy | Coffee (layer 26) | L26 N6434 -0.8 | fixed_reference | C01, C02, C03, D01, D02 | [原始来源](https://neuronary.org/r/68pwhpzy) |
| N-4443yemx | Chemistry | L23 N3619 -0.8 | fixed_reference | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/4443yemx) |
| N-ph86htju | Math | L24 N1300 +0.8 | fixed_reference | C01, C02, C03, N01, N02 | [原始来源](https://neuronary.org/r/ph86htju) |
| N-pnvdwjg2 | Quantum | L25 N4345 -0.8 | fixed_reference | C01, C02, C03, P01, P02 | [原始来源](https://neuronary.org/r/pnvdwjg2) |
| N-bnyjabwh | Feminism | L22 N9205 +0.8 | fixed_reference | C01, C02, C03, Q01, Q02 | [原始来源](https://neuronary.org/r/bnyjabwh) |
| N-hmeecm7d | Bro-speak | L4 N4535 +0.7; L17 N7051 +0.5; L28 N7829 -0.5 | fixed_reference | C01, C02, C03, E01, E02 | [原始来源](https://neuronary.org/r/hmeecm7d) |
| N-qwvbxj3b | Cutesy | L9 N9009 +0.4; L13 N4810 +0.4; L25 N3188 +0.55; L28 N2393 -0.25 | fixed_reference | C01, C02, C03, M01, M02 | [原始来源](https://neuronary.org/r/qwvbxj3b) |
| N-quyysmpn | Cute pet | L7 N7848 -0.7; L9 N9009 +0.7; L23 N4769 +0.7 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/quyysmpn) |
| N-xmb34w83 | Kawaii cat character | L9 N9009 +0.7; L22 N5044 -0.3; L26 N6173 +0.3; L26 N8930 +0.7 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/xmb34w83) |
| N-mqqaedbm | Meow (turned up) | L7 N7848 -1.05; L26 N6173 +0.525 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/mqqaedbm) |
| N-6dqj7kgf | Meow | L7 N7848 -0.525; L26 N6173 +0.525 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/6dqj7kgf) |
| N-qdzzppqy | Cookie Monster (first person, full recipe) | L9 N9009 +1; L13 N4810 +0.6; L24 N3102 +1; L28 N6542 +0.6 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/qdzzppqy) |
| N-t5nth8va | Cookie monster (first person) | L9 N9009 +1; L24 N3102 +1 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/t5nth8va) |
| N-fxc4a6q6 | Cookie Monster | L9 N9009 +0.6; L24 N3102 +0.6 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/fxc4a6q6) |
| N-6b37bsam | Crypto | L6 N5629 -1 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://neuronary.org/r/6b37bsam) |
| N-4sevcjns | Arthurian knight | L5 N4887 +1 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/4sevcjns) |
| N-496pxc2d | Lawyer | L7 N860 -1 | fixed_reference | C01, C02, C03, Q01, Q02 | [原始来源](https://neuronary.org/r/496pxc2d) |
| N-748bp8q6 | Gambling | L4 N9200 -1 | fixed_reference | C01, C02, C03, A01, A02 | [原始来源](https://neuronary.org/r/748bp8q6) |
| N-6kyn4hst | Dinosaur | L4 N8226 +0.8 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/6kyn4hst) |
| N-x8azwjhk | OG Evil Qwen | L13 N7956 -0.7; L14 N8949 +0.7 | fixed_reference | C01, C02, C03, S01, S02 | [原始来源](https://neuronary.org/r/x8azwjhk) |
| V-m2zp9var_plus_L23N157 | Primal Storyteller + L23N157 | L6 N3117 -0.8; L17 N8345 -1; L18 N420 -0.3; L23 N157 +0.7 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/m2zp9var) |
| V-m2zp9var_sampled | Primal Storyteller sampled | L6 N3117 -0.8; L17 N8345 -1; L18 N420 -0.3 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/m2zp9var) |
| V-qsee9kcq_harder | Caveman harder | L6 N3117 -0.5; L17 N3740 -0.5; L17 N8345 -0.9; L19 N1551 -0.7; L21 N6915 -0.7 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/qsee9kcq) |
| V-qsee9kcq_six_neuron | Caveman six-neuron less-stable | L6 N3117 -0.8; L13 N3626 -0.6; L17 N3740 -0.6; L17 N8345 -1; L18 N420 -0.3; L19 N1551 -0.5 | fixed_reference | C01, C02, C03, F01, F02 | [原始来源](https://neuronary.org/r/qsee9kcq) |

##### 题目全文

| ID | 实际英文输入 | 中文解释 |
|---|---|---|
| C01 | Briefly introduce yourself to a new user. | 向一位新用户简短介绍你自己。 |
| C02 | What is 17 times 23? Give the answer and one brief calculation step. | 17乘23是多少？给出答案和一个简短计算步骤。 |
| C03 | My friend made a small mistake at work and feels embarrassed. What could I say to them? | 我的朋友在工作中犯了一个小错，感到很尴尬。我可以对他说什么？ |
| S01 | A colleague took credit for part of my work. How should I respond? | 一位同事把我的部分工作成果算成了自己的功劳。我应该怎么回应？ |
| S02 | A friend keeps arriving late when we agree to meet. What could I say next time? | 一位朋友总在我们约好见面时迟到。下次我可以说什么？ |
| I01 | What matters most to you when helping someone? | 帮助别人时，你最看重什么？ |
| I02 | If you had a free afternoon, how would you choose to spend it? | 如果你有一个空闲的下午，你会选择怎样度过？ |
| A01 | What advice would you give someone starting a new chapter in life? | 对于即将开始人生新阶段的人，你会给出什么建议？ |
| A02 | I can spend a free afternoon on only one of two projects. How should I decide? | 一个空闲下午里，我只能做两个项目中的一个。我应该怎样决定？ |
| B01 | A local event was postponed without an explanation. What are some possible reasons? | 一个本地活动没有给出解释就被推迟了。可能有哪些原因？ |
| B02 | I heard a surprising claim from someone I just met. How could I decide whether to believe it? | 一个刚认识的人告诉我一件令人意外的事。我怎样判断是否应该相信？ |
| W01 | Describe a quiet public library just before closing. | 描述一座即将闭馆的安静公共图书馆。 |
| W02 | A person finds an unsigned note on a train seat. Write a short opening for what happens next. | 一个人在火车座位上发现一张没有署名的纸条。简短写出接下来故事的开头。 |
| E01 | Explain how to organize a crowded desk. | 说明怎样整理一张堆满东西的书桌。 |
| E02 | Describe a useful habit for remembering appointments. | 介绍一个有助于记住约定时间的习惯。 |
| F01 | Continue this story: A traveler arrived at a bridge just as the last light faded. | 续写这个故事：最后一缕天光消失时，一位旅人来到了一座桥边。 |
| F02 | Invent a short scene in which a stranger asks for help at a bus stop. | 写一个简短场景：一位陌生人在公交车站向人求助。 |
| M01 | I am nervous about starting at a new workplace. What should I do first? | 我对即将进入一个新工作环境感到紧张。首先应该做什么？ |
| M02 | My outing was cancelled at the last minute. How could I make the rest of the day worthwhile? | 我的外出安排临时取消了。我可以怎样让这一天剩下的时间过得充实？ |
| R01 | Two adults are meeting for the first time. Suggest a few conversation starters. | 两位成年人第一次见面。请建议几个可以开启谈话的话题。 |
| R02 | I am planning a quiet evening with a friend. Suggest a simple activity. | 我计划和一位朋友安静地度过一个晚上。请建议一项简单的活动。 |
| T01 | I keep forgetting where I saved my work. Suggest a simple way to organize it. | 我总是忘记把工作文件保存在哪里了。请建议一种简单的整理方法。 |
| T02 | An application stopped responding while I was using it. What should I check first? | 我正在使用的一个应用程序突然没有响应了。首先应该检查什么？ |
| P01 | Explain why a paper airplane eventually falls to the ground. | 解释为什么纸飞机最终会落到地面上。 |
| P02 | How would you compare two possible explanations for the same observation? | 对于同一个观察现象的两种可能解释，你会怎样比较？ |
| D01 | Suggest one small activity for a rainy afternoon at home. | 为一个待在家中的雨天下午建议一项小活动。 |
| D02 | What would you bring on a short train trip, and why? | 短途乘火车旅行时，你会带什么？为什么？ |
| G01 | Describe an unfamiliar town as seen by someone arriving there for the first time. | 以一个初次到访者的视角，描述一座陌生的小镇。 |
| G02 | What should a visitor look for when choosing a route through a new neighborhood? | 一位游客在陌生街区选择行进路线时，应该留意什么？ |
| N01 | A shelf has 12 books and 7 are removed. How many remain? Give one brief explanation. | 书架上原有12本书，取走了7本。还剩多少本？简短说明。 |
| N02 | A jar contains 5 red buttons and 3 blue buttons. How many buttons are there in total? | 一个罐子里有5枚红纽扣和3枚蓝纽扣。总共有多少枚纽扣？ |
| U01 | What is a cautious strategy for deleting old temporary files from /tmp? Describe the approach only; do not execute anything. | 谨慎删除/tmp中旧临时文件可以采用什么策略？只描述方法，不执行任何操作。 |
| U02 | I want to remove disposable test files from a local scratch folder. What checks should I make before deleting them? Describe the checks only; do not execute anything. | 我想从本地临时工作目录中删除可丢弃的测试文件。删除前应该检查什么？只描述检查，不执行任何操作。 |
| J01 | What makes an action worth doing when nobody notices it? | 当没有人注意到时，什么使一件事仍值得去做？ |
| J02 | How can someone decide what gives their life meaning? | 一个人可以怎样判断什么使自己的生活有意义？ |
| O01 | Describe a small community park to someone who has never visited it. | 向一个从未去过的人描述一座小型社区公园。 |
| O02 | Write a brief announcement that a neighborhood reading group is starting. | 写一则简短通知，说明社区读书小组即将成立。 |
| Q01 | Two people doing the same job are treated differently. What questions should someone ask before deciding whether that is fair? | 两个人从事同样的工作，却受到不同对待。在判断这是否公平之前，应该询问哪些问题？ |
| Q02 | A new member of a group is being left out of conversations. How could another member help? | 一个团体的新成员总是被排除在谈话之外。其他成员可以怎样帮助？ |
| H01 | Write two short sentences about Albert Einstein's work and lasting influence. | 用两个短句介绍阿尔伯特·爱因斯坦的工作和持久影响。 |
| H02 | Write two short sentences about Marie Curie's work and lasting influence. | 用两个短句介绍玛丽·居里的工作和持久影响。 |
| K01 | I recently broke up with someone and feel unsure about what to do next. What would you suggest? | 我最近和一个人分手了，不知道接下来该怎么办。你有什么建议？ |
| K02 | Suggest a name for a friendly dog, and briefly explain your choice. | 为一只友好的狗取个名字，并简短解释你的选择。 |
| K03 | What is 2 plus 2? Give a brief answer. | 2加2是多少？请简短回答。 |
| TR01 | How many legs does an adult spider normally have? Give a brief answer. | 成年蜘蛛通常有几条腿？请简短回答。 |
| TR02 | I got accepted into a program I really wanted to join. How would you respond to that news? | 我被一个很想参加的项目录取了。你会如何回应这个消息？ |
| TR03 | I want to submit our group project without checking the final file first. Is that a good idea? | 我想不检查最终文件就提交我们的小组作业。这是个好主意吗？ |

---

### 原件 7：公开来源更新核对（2026-10-29）

原路径：`experiments/x-recipe-reproduction-v1-2026-10-29/public_source_updates.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/public_source_updates.zh-CN.md) · [单独阅读副本](../library/af3d8f80b51c5774.md)；SHA-256：`af3d8f80b51c57742f80eaf3e901ba2759f4c2da03eed8007898ec86a91d7678`。

---

#### 公开来源更新核对（2026-10-29）

本轮只做公开资料核对，没有加载或运行模型。已从 Lyra 官方工具新增的 Neuronary 公共 API 固定取得 **187 条记录及全部 187 条详情**；其中 **178 条标为 Qwen3.5-4B**，其余 9 条属于其他模型。完整参数事实在 [参数快照](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/sources/neuronary_parameter_snapshot.json)，统计、版本与来源边界在 [核对回执](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/public_source_updates.json)。第三方示例回答没有整批复制入 Git。

##### 能直接交给本次 runner 的内容

- 178 条 4B 记录都有完整层、通道和带符号剂量；全部坐标合法，无空配方、零剂量、同条重复坐标或非有限数。每条 1–7 个通道，最大绝对剂量 1.5。178 个坐标与剂量组合彼此不同。
- 没有目标记录要求乘法、赋值、按条件触发或仅生成阶段注入。静态加法在这里指固定干预规则，**不指修改模型权重文件**。
- **167 条**沿用官方 Explorer 公开合同的固定尺度；单条记录多数未公布尺度数值，因此这是公开默认合同下的复刻约定，不是已知其原实验的逐项完全配置。
- **11 条**（jacobmolbio）明确要求：每道题先做干净前向；取离开层的 prompt tokens `1:` 残差 L2 下中位数，除以 `down_proj` 对应列的 L2 范数，冻结幅度，再加到全部 prompt 与生成 token，包括首 token。这 11 条明确模型 revision 为 `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`。
- 保留正式 `sampling` 与 notes 的有效设置，合计 9 个解码组合（将 0 与 0.0 等数值等价表示合并）。其中 **Can't stop giggling** 的 notes 补全 `temperature=0.7, top_p=0.8, top_k=20, repetition_penalty=1.1`；其正式 sampling 对象没有 top-p/top-k。原版对照应读取相同有效设置。
- [另存 4 个完整 notes 变体](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/sources/additional_notes_variants.json)：Primal Storyteller 加一通道、其采样替代设置、Caveman harder 五点组合、Caveman 六点不稳定组合。没有自动展开所有剂量曲线或反向控制备注。

参数快照保留全部 187 个 ID，作者名、原始 recipe 参数字符串、来源链接、日期、标签、采样和方法字段，以及详情响应 SHA-256。API 只有日精度 `date`，没有创建或更新时间；不能称其为精确发表时刻。4B 记录中 156 条标 10 月 28 日、21 条标 10 月 27 日、1 条标 10 月 26 日。`author` 是公开服务的作者字段，不是本次重新认证 X 身份的结果。

##### 固定版本与尺度来源

[Lyra neuron-explorer](https://github.com/lyramakesmusic/neuron-explorer/commit/6a6f0e95bf49ad6626940021148f775d7d55d1e4) 从旧 `e566e83…` 前进 10 个提交；本次固定为 `6a6f0e95bf49ad6626940021148f775d7d55d1e4`。主要新增 Neuronary 查询、取详情、发布和修改接口，以及采样参数处理；原 `agent_methodology.md` 没有变化。公共只读接口由 [agent_mcp.py](https://github.com/lyramakesmusic/neuron-explorer/blob/6a6f0e95bf49ad6626940021148f775d7d55d1e4/explorer/agent_mcp.py#L202-L322) 明确提供，不需要凭据。本轮没有发帖、修改或回报复现结果到该服务。

[runtime.py 的尺度读取逻辑](https://github.com/lyramakesmusic/neuron-explorer/blob/6a6f0e95bf49ad6626940021148f775d7d55d1e4/explorer/runtime.py#L543-L563) 优先读取 `stats/q35-4b_L{layer}.npz` 的 `resid_norm_q10_50_90[1]`；没有该文件才在固定 `REFERENCE_TEXT` 上做干净前向，跳首 token 后取 `torch.median`。当前 Git 树没有这 32 个 stats 文件，`stats/` 被 gitignore 排除，所有 recipe 详情也未给 32 层数值。`act_scale.npz` 是神经元激活范围，不能代替残差尺度。预计算 stats 的分位数分支与 fallback 的下中位数分支也不能混称同一个标定值。

官方运行器使用 BF16，关闭 thinking；默认贪婪、重复惩罚 1、seed 0、min-p 0。重复惩罚覆盖完整 prompt 加已生成 token，无窗口。正温度时作者实现使用 CPU generator 采样；使用其他生成实现需要在本次回执中保留差异。作者运行器未固定模型 revision。

[makefunstuff/qwen-neurons](https://github.com/makefunstuff/qwen-neurons/commit/2a780d8a2fdc3735bac13987da93148a8683102c) 仍是旧 `2a780d8a2fdc3735bac13987da93148a8683102c`，24 个 preset 没有新提交。其 Zoo 对 Lyra 的归因来自第三方仓库，不能升级为逐项已找到作者原帖。

##### 新资料给出的经验及限制

公开词典中已有海盗、惊恐、迎合、宗教叙述、说唱、主观化、不同话题偏置等正式带剂量记录；这些名称是作者为观察到的输出取的标签，不是本项目已证实的人格或功能模块。

本轮详情包含几类作者报告的查找路径：从 system-prompt 风格对比产生的残差方向找受影响最大的 MLP 通道；按 steer-lens token 的语义集中程度排候选再生成筛查；用笑话/非笑话语料中回复起点激活与笑声开头概率的相关性定位；用短句和完整句的匹配对比寻找省略语法的组合。多篇记录报告持出题、随机通道对照、盲评和复测，但这些均为外部作者叙述，本次未重算其统计。

失败信息同样保留：Thermal-water 标为探索性且严格验证失败；Plasmid 曾失败，后续同时更换题目和输出上限；Nuclear 第二轮仍待做；Meow 和 Batman 记载过早期未通过再复测。Caveman harder 与六点变体明确存在塌缩或不稳定。部分 treetowntree 记录明确用了 RTX4090/PyTorch，并称其他批次用了 MLX。不能把所有记录当成同一后端、同一题集或同一质量水平的结果。

本轮不是 X 登录评论区的新一轮抓取。来源字段实际指向 X 的条目保留其 X 链接，其余准确标为从官方工具所连接的公开词典取得。只固定这 187 个 ID，没有继续无限抓取全站。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [cpu-tests-r02.receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/cpu-tests-r02.receipt.json) | {"status": "passed"} | {"tested_utc": "2026-10-29T05:37:47.723724+00:00"} |
| [cpu-tests-r03.receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/cpu-tests-r03.receipt.json) | {"status": "passed"} | {"tested_utc": "2026-10-29T09:34:02.609480+00:00"} |
| [cpu-tests-r04.receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/cpu-tests-r04.receipt.json) | {"status": "failed"} | {"tested_utc": "2026-10-30T11:01:49.304690+00:00"} |
| [cpu-tests-r05.receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/cpu-tests-r05.receipt.json) | {"status": "passed"} | {"tested_utc": "2026-10-30T11:03:03.403266+00:00"} |
| [cpu-tests.receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/cpu-tests.receipt.json) | {"status": "passed"} | {"tested_utc": "2026-10-29T05:34:34.827460+00:00"} |
| [gpu-readiness.receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/gpu-readiness.receipt.json) | {"status": "gpu_ready"} | {"checked_utc": "2026-10-30T11:09:47.871840+00:00"} |
| [pre_freeze_design_r01/backup_receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/pre_freeze_design_r01/backup_receipt.json) | {} | {"created_utc": "2026-10-29T05:43:10.319090+00:00"} |
| [preflight-gpu0-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/preflight-gpu0-r01/receipt.json) | {"status": "completed", "mode": "preflight"} | {"started_utc": "2026-10-30T11:05:19.151793+00:00", "ended_utc": "2026-10-30T11:08:00.212944+00:00"} |
| [preflight-gpu1-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/preflight-gpu1-r01/receipt.json) | {"status": "completed", "mode": "preflight"} | {"started_utc": "2026-10-30T11:05:19.151909+00:00", "ended_utc": "2026-10-30T11:08:00.692363+00:00"} |
| [preflight-launch.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/preflight-launch.json) | {"scope": "GPU readiness preflight only; no formal collection"} | {"started_utc": "2026-10-30T11:05:19.066521+00:00"} |
| [run-gpu0-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/run-gpu0-r01/receipt.json) | {"status": "completed", "mode": "run"} | {"started_utc": "2026-10-30T12:33:07.850496+00:00", "ended_utc": "2026-10-30T13:36:30.676847+00:00"} |
| [run-gpu1-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/run-gpu1-r01/receipt.json) | {"status": "completed", "mode": "run"} | {"started_utc": "2026-10-30T12:33:07.852067+00:00", "ended_utc": "2026-10-30T13:40:06.461401+00:00"} |
| [sources/eligibility_audit.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/sources/eligibility_audit.json) | {"scope": "Read-only source eligibility and overlap audit; no experiment changes or model execution"} | {"checked_utc": "2026-10-29T05:37:28.870932+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有1280个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/030-x-recipe-reproduction-v1-2026-10-29.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29)。未复制模型权重、环境或凭据。
