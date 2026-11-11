# 136．WSP VLM开放工具v6

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-05；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

从行为筛查转入开放内部测量和非梯度权重修补闭环，准备给研究者反馈工具。

**实际过程、结果与后来更正**

保留本版本工具、验收、搜索启动身份及原始回执；后续v7/v8结果分版本列，不把后继成绩倒填到v6。

**来源身份**：`wsp-vlm-open-repair-v6-2026-11-05`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：WSP-VLM 总方案 v2：开放诊断与反馈驱动的权重修补

原路径：`docs/wsp-vlm-ai-repair-plan-v2-2026-11-05.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-vlm-ai-repair-plan-v2-2026-11-05.zh-CN.md) · [单独阅读副本](../library/957f20dc8745ca70.md)；SHA-256：`957f20dc8745ca70c1844bc590e035141baa24e0b8a45e829050687623054394`。

---

#### WSP-VLM 总方案 v2：开放诊断与反馈驱动的权重修补

##### Material Passport

- 日期：2026-11-05；工作流：academic-research-suite / experiment-agent / plan。
- 状态：方案修订；未运行实验。真实模型结果 UNVERIFIED。
- 本版是当前总流程入口，取代旧视觉方案的“两层/128列/仅MLP”及筛查文件中“仅从预设错误类型选择诊断”的约束。B/C已冻结数据、主终点、提示、筛查统计和12小时预算保持不变。
- 配套：[设计者自查](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-vlm-ai-repair-self-check-v2-2026-11-05.zh-CN.md)；[筛查时间安排](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-vlm-bc-timeline-v1-2026-11-05.zh-CN.md)。本轮授权仅修订、自查和文档交付，不含模型加载、前向、激活提取、研究者模型调用或权重试改。

##### 1. 中心猜想与方法逻辑

一部分VLM错误可能具有跨实例共享、可以通过少量权重变化改善的计算环节。研究者AI能够根据失败和成功对照、内部测量、试改后的修对/改错反馈，逐步寻找有用的修改。**失败原因、修改位置、层数、支持集合与编辑算法都应是研究过程的选择，而不是人类提前给出的答案。**

该猜想可以失败：错误可能分散、能力不足、需要更广泛适配，或所有可行补丁都有较大损伤。行为差异不证明内部原因，内部可读出不证明可修，稀疏补丁有效也不自动证明研究者AI优于其他搜索。

这里借鉴的是作者的“给目标和工具→诊断→局部修改→实际测试→反复修订→冻结”的逻辑。原作者初始提示没有锁定L15/L19或MLP；50-pass最终选择两层，10/25-pass其他运行分别涉及更广矩阵或注意力头。人类提供了诊断与配对评价方法提示，不能称完全无先验的自主发现。[初始提示](https://github.com/RikiyaT/lm_understand-logs/blob/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/exp8_math/runs/p50c/turns/t001/prompt.txt)；[实验8运行说明](https://github.com/RikiyaT/lm_understand-logs/blob/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/exp8_math/README.md)。

##### 2. 审计发现：哪些锁死了，哪些没有

| 已有位置 | 实际问题或现状 | 本版处理 |
|---|---|---|
| 旧 `wsp-visual-evidence-plan-v1` §1.2/§4/退出规则 | 只改文本MLP down_proj，最多两层/128列；排除视觉、融合、注意力；只给两种算子 | 明确废止为历史方案，不继承其层/列/算子/12候选及范数上限，也不继承其痛点方向和效果阈值 |
| `wsp-vlm-behavior-screen-v1` §5.2 | 已写不预定两层/MLP-only，允许视觉编码到解码；不存在当前“两层”硬规则 | 保留这一开放原则，进一步明确可写参数范围与反馈循环 |
| 筛查v1 §3.1/§4.2、时间表§3 | D仅从预登记类型选诊断，容易把人类的“忽略条件/被图像带偏”当唯一入口 | 全部D反馈开放检查；预设类型保留为固定统计项，AI可另建新分类，区分探索与确认 |
| 筛查v1 §5流程 | “先定位有作用的位置，再生成补丁”容易变成必须先证明完整病因才能试改 | 定位与试改交替。探索性权重试改本身可以是诊断；先给可检验预期，不要求完整机制证明 |
| 三类候选算子、稀疏列写法 | 容易被实现成固定算子菜单或列级编辑器 | 算子仅示例；采用通用参数差分合同，允许AI提出新的非梯度编辑计算，按同一预算与验证规则执行 |
| v5 `runner.py`/`launch.py` | 仅原版P0/D/H推理，既没有两层白名单，也没有权重试改/研究者循环 | 不把“没有白名单”冒充编辑器已完成；本次不改已验收筛查代码。后续编辑服务另做版本化实现 |
| B/C统计代码 | 计算固定错误模式和主终点；没有检查层号或编辑位置 | 保留统计代码与历史数值口径；新AI分类另存记录，不能静默改主检验 |

本次审计范围为上述VLM方案、v3/v5运行器及B/C评分入口，不声称其他历史数学或编程实验全部经过审计。

##### 3. 哪些固定，哪些交给AI

###### 3.1 固定的是任务、公平评价与资源边界

- 目标模型固定Qwen/Qwen3-VL-4B-Instruct，revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`；主比较固定同输入、同处理器/模板、同生成设置、同评分规则。S0沿用BF16、SDPA、batch=1、greedy、最多128新token及既定处理器面积范围65,536–1,048,576；修补阶段若有必要改协议，须在搜索前另行冻结并重建匹配基线，不能混用旧分数。
- 正式修补评价不能靠改答案解析、改图、改token上限、插入答案、换模型或逐题外部路由获得收益。
- 目标产物为相同架构/张量名/形状的静态权重补丁。冻结后普通推理不用研究者AI、不保留诊断hook、不逐题查答案。
- 首轮采用非梯度权重修补，不对目标权重做梯度训练或把训练更新藏在编辑工具中。求导若仅用于诊断/归因测量，可在计账工具和预算内使用，不能因此禁止一种诊断线索；诊断求导不授权梯度更新。闭式拟合若使用标签/提示目标须披露监督来源，不能称无监督或无拟合；若日后要梯度训练，明确改为混合/训练比较方法，另核预算。
- 搜索前必须冻结总调用/实际样本与token/CPU与GPU时间/研究者费用上限、临时修改总量与最终稀疏标量上限、开发评分规则、保护退化界限及确认程序。按总量约束，不把“最多两层”当成本替代。
- 所有模型前向与干预评估走受计账服务；算子代码不能私下运行模型绕过额度。不得读取封存终验数据。原权重及所有候选、失败、回滚均保留。

这些约束用于回答“是否真的修好了以及花了多少成本”，不提供故障位置或正确编辑配方。

###### 3.2 AI可以决定和修订的内容

| 自由度 | 具体允许 |
|---|---|
| 失败解释 | 从所有开发回答重新分类；提出或撤回重复生成、条件遗漏、识别困难、数字偏好、格式行为等假设。预设B/C解释只是线索 |
| 诊断操作 | 选择成功/失败对照、输入位置、层与模块，读取权重/激活/输出，提出临时干预或直接权重试改；探针不是必经阶段 |
| 修改位置 | 模型已有可写浮点参数：视觉编码器、融合/投影模块、语言解码器的注意力及MLP，以及有针对性依据的其他参数；不预定前/后层、层数、头数或列数 |
| 参数表示 | 标量、行/列、头块、局部矩阵或多个模块联合差分；最终按实际变化的唯一标量计数，低秩不等于支持稀疏 |
| 修改计算 | 缩放、投影、方向增减、闭式补偿或AI提出的其他符合合同的非梯度编辑；公式列表不作为白名单 |
| 搜索路线 | 依据反馈改变位置、强度、方向、支持、算子、父候选或失败解释；可撤销、回原版、组合候选或尝试更稀疏版本 |

不自动沿用原作者对embedding/最终norm等的排除：本版允许有针对性的现有参数编辑，并记录张量绑定、数值和实际效果。这个自由度是我们的应用设计，不声称逐条复刻原作者实验。统一缩放整个网络或只改输出温度不作为本项目“有对象的局部修复”产物；若作为诊断参照，单列计账。

搜索范围广不等于每轮全网扫描或任意密集改动。AI提出某次测量/修改时需说明要区分什么、在哪里作用、如何计账；可以在预定临时标量预算内先测较宽候选再压缩，最终必须满足更严格的稀疏上限。零收益时不自动扩上限。若绑定权重导致一个逻辑编辑实际影响多个位置，按实际存储/绑定及功能范围记录，不能假称只改一个独立位置。

##### 4. 从发现失败到多轮修补的完整流程

###### S0：原版筛查，先获得真实行为

沿用P0→B_D/C_D→登记→B_H/C_H。B146组（D58/H88）、C160组（D64/H96），7,568正式请求＋64工程请求；现有尝试上限7,888、累计12 GPU小时仅用于该筛查。普通/规则提示、问法/顺序与主判据不变。到此尚不修改目标权重。

AI在D反馈出现后即可阅读全部开发输出、正确标签与规则，不只接收人类挑中的错误例；成功对照、反例、格式问题及强提示改坏的例子也交付。资料中区分原始结果、文献先验和人类解释，不把后两者当观测。H尚封存。

既定错误模式继续按原定义计数。AI可以在D提出新模式，保存可操作定义、例子、反例与分母；在任何H输出前固定要检查的描述。原H主终点/Holm不改；新模式先作为探索性复核报告，不自动借用主检验显著性或事后构造新主终点。H之后才提出的模式不能称本轮前瞻确认。

原优先级阈值是两个预设行为对比的资源选择规则，不是WSP能修的普遍条件。未达主阈值但发现另一种失败，可保存探索证据、提出后续有对照的验证；不能借此自动跳进搜索、改原阈值或追加本轮请求。模式≥8/12组只表示既有线索强弱，不要求AI只围绕该模式解释。

###### S1：建立修补会话，明确可见数据与预算

筛查后至多选择一个优先对象。研究者获得原版权重只读基线、允许的开发数据及完整失败反馈、任务指标与保护项、实际架构/工具接口；不提供指定层号、确定机制或最终补丁公式。B优先关注有空间条件的计数，C优先关注冲突下的通常问句，但AI可以判断它们由不同原因造成。

D及已经看过的H可以转为编辑开发材料，身份明确改为“已见”；它们不能再承担最终补丁独立确认。搜索前另行备好来源组隔离的修补确认集，避免同组图/改写跨集；必要时设对象/素材不重叠子集并声明剩余共享。新集数量、效应/保护界限与功效需在有基线后冻结。当前这份新数据尚未准备，不能假称现有H就是它。

搜索执行合同的数值空项必须在第一次修改前填完，AI不能自己扩预算。本版先冻结流程，不凭未测基线拍定最终稀疏比例、收益门槛或搜索轮数；不沿用旧12候选/两层/128列，也不机械照搬作者50个pass（其pass是批量请求，不等于50题）。

###### S2：每一轮的研究单元

| 顺序 | AI／执行服务做什么 | 留下的证据 |
|---|---|---|
| ①读取反馈 | 查看原版或父候选的真实回答、评分、修对/改错、失败类别、内部测量及已用预算 | 输入反馈包hash、可见数据ID、当前父候选hash |
| ②提出可检验想法 | 说明怀疑的失效、支持与反例、下一步预期；选择内部诊断、临时干预或直接权重试改 | 简短诊断说明及预期，允许“证据不足、先探索” |
| ③提交操作 | 指定模块/位置/支持和计算代码，或请求新测量；服务检查数据权限、数值、形状/绑定、预算 | 实际操作清单、代码与参数、预计成本、通过或拒绝理由 |
| ④执行试改和配对测试 | 从明确父候选应用差分，真实推理；在同组完整开发题上比较原版、父候选与新候选 | 原始输出、分格/联合正确率、修对/改错、格式/截断、成本 |
| ⑤根据证据更新 | 保留、回退、换点、换强度、换算子、改变解释，或停止；下轮回到① | 接受/拒绝原因、当前最佳与当前实验候选分开保存 |

不是每轮都必须先读激活，也不是每个诊断请求都必须马上生成补丁。一次定向权重试改可能同时提供定位证据和性能反馈。它之前需要可解释的操作和预期，不需要先完成全套机制证明。一个候选失败可以否定本次位置/强度/公式，不能自动否定整类方法；也不能因为失败就无限换任务。

为避免累积编辑身份混乱，每个候选保存相对原版W0的完整有效ΔW与父候选关系；实际执行可以从W0重建。撤销回到明确hash，不把残留hook/cache或旧补丁带到下一轮。多个局部补丁合并后必须真实联合测试，不能相加局部收益。

###### S3：反馈和选择规则

开发阶段先满足预先冻结的保护/格式要求，再依据任务整体效果和损伤选择候选，平分时比较稀疏度/扰动与成本。B至少同报全部与子集、联合正确率；C同报五条件与联合正确率。不能只优化固定数字偏好、统一忽略图像或单一错误子类。

AI可以为诊断自选题和构造对照，但必须标明来源、标签/监督与用途；这样的局部结果只作线索。候选若要成为当前最佳，必须在预先固定的完整开发评价包上比较，不只测上轮失败题。原版基线可在严格同输入/设置下复用已保存答案；父候选已有完整结果也可复用，不能把缓存当新独立测量。变了设置则不能混比。

临时hook/激活干预的结果和静态权重补丁的结果分开记录；激活有效不保证权重可实现。研究者可请求多强度、替代位置或预算匹配参照来区分解释，但不强制每个微小候选都跑完整消融矩阵。只有支持具体机制主张时才要求对应的因果比较。

重复看开发集会过拟合；开发提高只用于搜索，不声称确认性显著。所有尝试包括失败/改坏都保存；耗尽预算、没有合格候选或AI判断证据不足均可停止，不要求必须输出有效补丁。

###### S4：冻结、重载、一次独立确认

在打开新确认结果前，冻结一个最终候选及所有比较方法的配置、模型/数据/代码hash。卸载重载，移除诊断hook，核对实际BF16变化支持与数值；最终以普通提示自然推理，并附强提示等对照。

新确认集上比较原版、规则提示、补丁、补丁＋规则提示，以及适用且已准备的近邻编辑/适配方法；所有方法有开发选择与独立确认隔离。主张稀疏修复需看到新数据收益和保护项表现；主张相对价值需看收益、损伤、泛化或包括搜索在内的总成本；不拿开发集提升替代。

确认失败也保留。若看到确认结果后再修改，该集立即成为已见开发数据；不能继续叫独立终验。新确认数据和预算不足时结束，不反复使用同一确认集选到成功为止。

###### S5：研究者AI贡献单独检验

补丁有效不等于AI研究流程更好。若要主张AI增量，需同可见信息、可修改范围、算子能力与计算/调用预算的脚本搜索，以及AI只见总分等比较，并报告独立搜索变异。

允许AI创造新算子会使“同算子空间”比较更难：不得事后把AI最好的算子送给脚本，只计脚本后续搜索成本，再称公平比较。可以报告复用发现的事后对照，但主张搜索优越性需预先定义共同能力边界、完整计入发现成本，或冻结算子库后开展新的独立比较。首个成功补丁不承担这一尚未完成的主张。

##### 5. 最小研究者任务说明（后续使用模板，当前未发送给任何模型）

> 目标是在固定模型、输入和评分协议下，通过直接修改目标模型已有权重，改善开发材料中可重复的失败，并保留指定控制任务。先检查全部成功与失败反馈；人类给出的B/C模式只是候选解释，你可以否定或重新分类。你可选择任何合同允许的现有参数位置，不指定层号、层数或MLP。根据证据选择读取、临时干预或直接试改；每次说明操作和预期。定位、修改和测试可以交替进行。所有前向/编辑须经受计账工具；每次保留原始反馈、差分与回退记录。遵守已冻结的标量、计算、费用、数据权限和停止限制；不得训练目标权重、改变评价或访问封存确认集。没有有效补丁时如实结束。

这段是方法指导，也属于人类先验，必须随实验公开。未来任务说明不能把“常识路由失效”“忽略空间条件”“重复循环”写成必须证实的事实，也不能附上原作者两层补丁作为答案。

##### 6. 工程与时间状态，避免把流程设计说成已就绪

| 部分 | 状态 |
|---|---|
| S0固定数据、原版筛查运行器、评分、CPU处理器验收 | 已有v2/v3/v5资产，真实P0尚未执行；两工作日目标仅覆盖筛查与交付 |
| D开放错误阅读/登记 | 本版已定义；既有runner仅要求非空description与D输出SHA，不锁错误类型；探索分类另存，不改原评分器 |
| 研究者会话与反馈服务 | 待指定研究者模型/版本、工具接口及信息隔离；未启动或收费调用 |
| 读取内部张量、临时干预、通用权重差分、可验证回滚/重载 | 尚未作为本VLM编辑服务实现和验收；不能拿原版推理器代替 |
| 搜索资源与评分合同 | 待冻结总调用/样本/token/时间/研究者费用、临时与最终标量上限、开发保护规则及停止条件；本轮无新增额度 |
| 新补丁确认数据与比较方法 | 尚未准备/冻结；需基线、可用新来源与功效支持，不能复用已见H充当新留出 |

因此总流程逻辑已明确，但S1–S5不是现成可启动的运行合同。后续先完成S0，拿到真实失败及吞吐，再填完这些具体执行项；无需为填空先固定两层或算子。任何有限实现只支持已开放范围内的结论；若缺少视觉模块等工具，报告工程缺口，不能把范围外不能修改解释为WSP失败。

##### 7. 当前文件关系

- [旧视觉方案](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-visual-evidence-plan-v1-2026-11-05.zh-CN.md)：历史记录，其“两层/仅MLP”及旧痛点不生效。
- [行为筛查v1](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-vlm-behavior-screen-v1-2026-11-05.zh-CN.md)：固定比较与统计来源；实际样本/工程由v2/v3/v5更新；诊断开放性和修补流程以本版为准。
- [时间表](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-vlm-bc-timeline-v1-2026-11-05.zh-CN.md)：保留P0/D/H顺序与筛查预算，D允许新模式；不承诺第3天完成补丁。
- [v5通道准备](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-channel-prep-v5-2026-11-05/README.zh-CN.md)：原版筛查准备状态，不是编辑循环实现。

本次不改变实验代码、数据、权重、已冻结统计或旧运行证据。只修订研究逻辑及当前入口，并明确已失效限制。

---

### 原件 2：原始文档

原路径：`experiments/wsp-vlm-open-repair-v6-2026-11-05/RESEARCHER.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/RESEARCHER.md) · [单独阅读副本](../library/2819e3988dfc5b28.md)；SHA-256：`2819e3988dfc5b288c3cec049b50d30a825a74b365dda304cefdea55762d6b26`。

---

You are the researcher. The human fixes task, evaluation, data access and costs.
You diagnose failures, choose measurements, select parameters, calculate edits and
revise your ideas using actual feedback. No layer, neuron ranking, or edit schedule
has been prescribed. No successful patch is required. You may stop with a negative
or inconclusive result. Explain your evidence, next action and expected observation
before exactly one fenced `python` or `forward` block. A plain final reply stops.

Python runs persistently on CPU in an isolated directory. NumPy is `np`.
`catalog()`, `NAMES`, `load_original(name)`, `load(name)`, `save_edit(name,array)`,
`drop_edit(name)`, `edited()` expose parameter inspection and staging.
You write the selection and modification algorithm yourself. No target-model
training or unmetered model execution is allowed. Disclose any labels/fitting used.
`EVIDENCE` contains only permitted development data; `ARTIFACTS` contains complete
tool feedback. Successful controls and failures are equally available. No sealed
confirmation data is accessible. Target-model prompts never receive gold labels.

`forward` JSON takes `op` and relevant fields:

- `status`: current, best, resource use. Start here or with `evidence`/`catalog`.
- `evidence`, optional `ids`: input, gold, prior raw answers; initial answers may
  be absent until original evaluation. Large results are paginated, not discarded.
- `image`, `request_id`, `kind` = `input` or `preview`: attaches a verified image
  to your next turn. You may request any allowed development example.
- `catalog`: parameter names/shapes/dtypes/tied aliases from the checkpoint.
- `runtime_catalog`: actual runtime named modules/parameters; counts wall/load cost.
- `measure`, `candidate`, `ids`, `spec`: teacher-forced internal readout. `spec`
  supports `continuation`, `score_token_ids`, `capture` and `interventions`.
  A capture supplies `module`, `where` (`input`/`kwargs`/`output`), `path` (tuple/dict keys),
  optional `flat_indices`. Results retain actual tensor shape, input token IDs,
  decoder image-token positions and image grid. Vision tensor axes require
  inspection; do not assume they are decoder-token axes. No arbitrary gradient
  diagnostic or attention-probability extractor is implemented yet.
  Temporary interventions additionally supply explicit `flat_indices`, `values`
  and `operation` (`add`, `replace`, `scale`); arbitrary replacement values may be
  calculated in Python. They do not become weight edits or best candidates.
- `commit`, `parent`, `rationale`: validate staged tensors and create an immutable
  candidate. Parent must equal current checkout. Actual effective scalars are
  counted against W0; tied parameters count once. Staging clears on commit.
- `checkout`, `candidate`: return to any recorded candidate or W0; clears staging.
  Python variables remain, so explicitly refresh arrays after checkout.
- `evaluate`, `candidate`, optional `ids`: paired original/parent/candidate outputs
  under identical inputs. Omitting ids evaluates the fixed full development pack.
  Local subsets are diagnostic only; raw answers and repaired/worsened IDs return.
- `accept`, `candidate`: observer applies the frozen full-development selection
  and protection rules. Failures do not automatically expand budgets or scope.
- `artifact`, `name`, optional `offset`/`length`: read a page of full returned JSON.
- `freeze`: freeze the current best within the final sparsity budget; ends search.
  This is a development selection, not evidence of independent generalization.
- `stop`, `reason`: end with an honest negative/inconclusive result.

Every tool operation (including errors), selected parent, code and result is logged.
Weight edits preserve architecture, tensor names and shapes. Do not alter scoring,
input images, generation settings or budgets. Final deployment must be ordinary
inference from a reloaded static patch with no diagnostic hooks. An engineering
tool error is not evidence against the scientific hypothesis.

---

### 原件 3：v6开放研究工具：实现与设计者自查

原路径：`experiments/wsp-vlm-open-repair-v6-2026-11-05/SELF_CHECK.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/SELF_CHECK.zh-CN.md) · [单独阅读副本](../library/d81d9ae82678c12f.md)；SHA-256：`d81d9ae82678c12fa73254df4ea193156a32fd37cd2dce38f6e52a63a5dfcf00`。

---

#### v6开放研究工具：实现与设计者自查

##### Material Passport

- 2026-11-05；同一助手自查，不是独立审查。依据`docs/experiment-design-self-check.zh-CN.md` v1。
- 本轮是已批准总方案v2的工具实现与离线工程验收；没有新增科学实验矩阵、冻结实际搜索额度或改变B/C筛查主终点。
- 证据入口：[实现说明](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/README.zh-CN.md)、[源码复用hash](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/reuse.json)、[测试回执](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/audit/offline_receipt.json)、[问题修正记录](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/audit/corrections.json)。

##### 设计卡

1. **主线/本轮问题：** 能否让研究者AI根据VLM失败反馈提出解释、自选参数与计算方法、反复试改和评价；本轮验证工具是否允许并可靠记录这一过程。
2. **增量：** 从原版筛查运行器推进到有候选身份、跨模块读写、开发评价、反馈和回滚的开放接口。工程增量有价值，但没有新增模型机制/有效性证据。
3. **依据与反例：** 复用数学开放controller/broker/kernel及v5图文/旧B/C评分；不复用WCP固定选点和作者轨迹重放。最不利情况是所有离线测试成功而真实模型接口不兼容或AI找不到有效补丁，均保留为可能。
4. **操作：** 真实后端代码固定Qwen3-VL-4B-Instruct既定revision/BF16/SDPA/greedy128；运行时枚举模块、AI提交任意合法参数值、实际BF16支持相对W0计数。此次只操作合成2×4数组、存量图片文件字节和代码，不触碰真实权重。
5. **估计对象：** 离线检查是代码协议、身份、隔离入口与清理行为；假后端修对不估计VLM收益。未来开发比较为同输入/设置的W0、父候选和新候选完整回答；局部测量不当主终点。
6. **判读：** 离线失败修实现；通过只表示已测试的控制流成立。真实工程异常停止，不计作任务错误。真实科学阴性须以后按冻结研究合同判读，当前不能下结论。
7. **范围/成本：** 本地CPU/文件验收；0真实权重反序列化、模型/处理器加载、研究者调用或GPU。B_D58/C_D64包复用已有图片；搜索预算、终验功效待真实基线。
8. **退出：** 配置未冻结、无授权、预算用尽、动作完成状态不明即拒绝/停止；AI允许无补丁退出。真实验收和搜索没有启动。

##### C01–C14

| 项 | 判定与理由 |
|---|---|
| C01 主线 | 通过。接口服务于反馈驱动的稀疏权重修补，不换成固定探针、两层定位或分类器训练 |
| C02 增量 | 工程范围通过。可提交/评价/回滚开放候选；不把合成涨分列作科学认识或论文结果 |
| C03 资产 | 通过。实际导入旧动作解析和B/C评分，改造旧命名空间/broker；固定hash。历史暂停和数值回执未动 |
| C04 假设 | 通过。允许没有可修位置、AI诊断错误、真实模块不兼容；离线通过不是可修性证据 |
| C05 操作 | 通过。静态权重、临时hook、teacher-forced测量、自然生成分开；候选有父ID与相对W0差分 |
| C06 路径 | 通过。原版/父/新候选共用输入和生成，真实参数修改后所有下游正常响应；临时hook另记不参加最佳选择 |
| C07 耦合 | 通过且真实验收待办。绑定别名计一次，冲突值拒绝，真实运行须对照storage绑定；不声称所有模块相互独立 |
| C08 归因 | 通过。只承诺反馈/候选控制链，不从假测量分数或单点修改推断模型病因、原生路径或AI优越性 |
| C09 区分 | 通过。离线两种反馈选出不同模块，证明协议可分支；测试脚本承担控制，不伪称研究者自主发现 |
| C10 指标 | 通过。复用完整答案评分；分格、主条件联合正确、格式、截断、修对/改错都返回。局部挑题不替代完整开发比较 |
| C11 失败 | 通过。基础设施异常单列，前向预留不退款，部分测量与失败Python候选保留，未完成动作不自动重放 |
| C12 成本 | 离线通过/实机待核。样本、token预留、实际token、CPU近似墙钟和总墙钟有记录；费用需账户外部上限，不能假装usage=实付金额 |
| C13 可信度 | 离线通过/实机待验。候选及缓存hash、动作幂等、D单独打包、确认函数不向AI开放；实际Linux权限及真实重载尚未验证 |
| C14 累积 | 通过。保留可复用工具与验收记录；下一步是有限真实工程验收和行为采集，失败可停，不自动扩大参数/任务/预算 |

##### 与前版的差别、相关历史错误

- 工具审计只列缺口；本版提供实现、配置模板、合成端到端轨迹和实际D导出。旧数学controller的50次强制结束、文本专用forward、单权重文件假设没有照搬。
- E02：没有把某两层当天然特殊点；选点代码由研究者提交。E03：支持数、有效dtype、L2分别记录，不称“少标量就小扰动”。
- E10/E11：测量/分数/探针不等于正确回答；所有候选以原始回答评分。E16：未知、失败、无补丁和工程异常都可结束，不强行救分。
- E22：D/H身份保留；已见H不能充当新确认。确认函数要求独立性审核凭据，检查组和图片字节重复；无法仅凭哈希证明素材/物体层面的独立性。
- E23：同助手自查和合成测试都不叫独立审查或模型复现。E24/E25：不要求完整机制才允许试改，也不一次实现所有高级诊断算法。
- 其余历史错误主要针对缓存机制因果拼接，本轮不作该类操作或主张，因此不适用；没有借此弱化源码、身份和数值检查。

##### 实质反方自查与修正

1. **“脚本本来就会选参数，不能证明AI自主。”** 接受。测试夹具故意是脚本，只验证同一工具能走不同路径；真实入口使用研究者回复，生产代码没有选层/排名算法。未来AI能力要真实会话和公平比较，当前不主张。
2. **“数值dtype不一致会夸大修改数。”** 已修正。即使checkpoint某张量F32，运行BF16时也先按BF16量化W0与候选再计数；增加F32→BF16不产生实际改动的反例测试。
3. **“复制旧后端仍看不到图或只测最后token。”** 图文输入按v5；研究者可请求原图/预览附件；capture按真实模块、张量路径和坐标返回形状，decoder图像位置和网格另记。视觉patch语义未验证，不强行等同decoder轴；真实teacher-forced边界不一致直接拒绝。
4. **“允许自由Python会绕过保护或读终验。”** 生产只用Linux隔离进程，原权重/候选/开发数据只读，工作区可写，无网络/GPU设备和整仓库挂载；观察者二次校验直接写出的NPY，防路径逃逸、形状欺骗、绑定冲突和超预算。文件接口不是OS隔离证明；本机未运行bubblewrap，必须真实机器验收。
5. **“缓存或上轮补丁残留造成假涨分。”** 缓存身份绑定模型/协议/输入/候选并校验内容hash；当前与最佳分开。候选每次从W0应用、finally恢复并检查，hook finally移除；替身验证异常路径，真实数值仍待核。
6. **“先修坏再只测好题，也能成为最佳。”** 局部结果不能accept；完整固定开发包比较并过保护/格式要求。配对返回全部修对与改错；保护损伤反例被拒绝。
7. **“失败途中结果丢了，看起来只剩成功。”** 评价逐条开始/完成/失败日志；内部测量逐条落盘；每次Python结束（含异常）保留合法可读取提案快照；动作完成未知不重放。已加部分测量失败、失败代码产生提案的检查。
8. **“换组ID就能将旧图作为独立确认。”** 修正为组登记＋图片字节哈希交叉检查，另要求来源独立性审核凭据。新组ID但同图会拒绝；近重复/重压缩仍依赖数据审计，绝不把当前同源合成夹具称独立科学证据。
9. **“旧HF快照是符号链接，隔离后找不到文件。”** 增加只做字节核验的模型视图准备器；不放宽为挂载整个缓存/仓库。本次未准备实机模型视图。
10. **“工程模式绕过验收就开始AI搜索。”** 搜索启动器只接受phase=search且要求真实工程验收记录；工程phase只用于以后独立受授权的底层工具验收，不能进入自主搜索循环。

结论：**本轮离线工程实现验收通过；真实运行验收尚未完成，科学猜想未检验。** 原总方案主线不变。配置默认关闭；不以本自查、GitHub提交或离线通过作为模型运行授权。

---

### 原件 4：WSP-VLM 自主诊断与修补：方案—代码能力核对

原路径：`docs/wsp-vlm-ai-tools-audit-2026-11-05.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-vlm-ai-tools-audit-2026-11-05.zh-CN.md) · [单独阅读副本](../library/5d7a68fa118209f1.md)；SHA-256：`5d7a68fa118209f112821469095d17c63ee298e1a77587f0920afbeccd4ded90`。

---

#### WSP-VLM 自主诊断与修补：方案—代码能力核对

##### Material Passport

- 日期：2026-11-05；身份：静态代码/准备度核对，不是实验结果或新执行授权。
- 目标：按原作者“人定目标和边界，AI提出诊断、写分析/编辑代码，工具执行并返回反馈”的分工，检查当前VLM能否闭环。
- 当前方案：[总方案v2](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-vlm-ai-repair-plan-v2-2026-11-05.zh-CN.md)。本次不改其任务、数据、指标、预算或方法边界。
- 核对方式：读取方案、源码、既有回执；用标准库计算文件哈希；未导入模型代码，未加载权重/处理器，未调用研究者模型或目标模型，未启动旧服务和远程任务。
- 来源快照：[文件哈希与范围](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-vlm-ai-tools-audit-2026-11-05.sources.json)。关键五份方案/代码与GitHub `e8ad1fbf8dcd54ae1c1e9d714a4598814958806d` 的blob逐一相符；v5六份代码与既有source_hashes全部相符。没有重新审计整仓库或当前服务器状态。

##### 1. 结论

**方案允许，当前VLM代码尚不能完成这个闭环。仓库已有可复用的开放式数学研究控制器，不需要从零重写；但它还没有接上Qwen3-VL的图像输入、内部测量和补丁执行。**

当前VLM原版运行链是：固定P0/D/H队列 → 固定原版模型 → 保存回答 → B/C评分。诊断登记只验证一段描述与D文件hash；不会自动调用AI诊断，更不会据此选神经元或修改权重。v5没有“两层”白名单，原因是它没有编辑功能，而不是已经支持任意编辑。

“会自主选点”的关键不是再写一个更复杂的固定排名算法，而是让AI能够读取证据、自己写排名/选择/修改代码，并让下一轮决策依赖真实反馈。

##### 2. 四套容易混淆的现成资产

| 资产 | 代码实际做什么 | 能否作为本项目自主修补入口 |
|---|---|---|
| VLM v5筛查运行器 | 固定原版Qwen3-VL、图文处理、生成、输出记录与预算；只接受P0/D/H | **不能直接用**。适合复用正确输入、生成、环境校验和记录部件 |
| 数学 `engineering-r2/controller.py` ＋ broker/kernel | AI返回自己写的 `python` 或 `forward` 请求；执行结果作为下一轮输入，有会话与原始记录 | **最接近所需分工，可适配**；当前路径、模型、工具和停止逻辑仍是旧数学任务 |
| `author_actions.py` 作者轨迹重放器 | 按公开日志的固定行取代码/请求并执行，禁止改科学代码 | **不能作为自主搜索入口**。它是重放现成研究路线，不会因新反馈重新想方法 |
| 编程WCP的editor/protocol/model_interface | AI只给错误打标签；脚本固定排名、选两层和8/32通道，再做列增益 | **不能原样移植**。会重新引入用户明确反对的固定配方；只能择取通用记录/评分思路 |

直接证据：

- [v5 runner](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-channel-prep-v5-2026-11-05/runner.py)：L21–29固定队列，L142–143固定原版加载，L154–181仅生成回调；L217–226只检查诊断登记。L195禁止同任务/阶段重复尝试，适合一次筛查，不是迭代候选调度器。
- [开放数学controller](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-process-reproduction-v1-2026-11-03/engineering-r2/controller.py)：L19–34解析AI代码/前向请求，L192–240把结果交回AI继续；L226–233仍要求50次成功前向才能正常结束，不能直接继承到新方案。
- [轨迹重放器](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-process-reproduction-v1-2026-11-03/author-code-reuse-r1/adapter/author_actions.py)：L61–94从固定日志行派发请求，与重新搜索不同。
- [WCP editor](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/editor.py)：L53–62明确要求只标注、不得推断神经元/编辑权重；[protocol](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/protocol.py)L40–55固定激活差排名、前两层和8/32通道；[model_interface](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/model_interface.py)L16–44限制通道数、增益[-1,1]及MLP down_proj。

##### 3. 按AI实际需要的动作列缺口

下表的接口名是能力说明，不代表这些VLM接口已经实现。可合并实现，不要求每行单建一套服务。

| AI要做的动作 | 已有可复用部分 | VLM还缺什么 | 准备完成应能证明什么 |
|---|---|---|---|
| **看失败、成功和原图** | v3图文队列与标签；v5保存完整回答、token、停止原因；B/C评分器 | 开发资料导出/查询：按来源组关联输入图、处理器预览、原回答、正确标签和各提示结果；受控图像查看或多模态反馈入口；新失败分类自由文本 | AI能检查成功与失败对照、提出新分类；不只拿到总分或人选的少数例子；目标VLM输入仍不包含金标准 |
| **持续提出下一步操作** | 数学controller有持久会话、代码块解析、反馈和重连记录；旧工程回执记4轮、1次前向集成通过 | 新VLM会话配置和任务说明；接入图像/Unicode反馈；把旧50-pass与轮次提醒改为已冻结资源/结束规则；选择当前研究者模型和锁定版本 | 同一个研究者会话能根据上一步结果改变操作；没有预排的候选清单、固定轮数救分或强制跑满50次 |
| **看架构、权重并自己挑点** | 数学CPU kernel提供NAMES/load/load_original及持久Python，允许AI写任意分析代码 | Qwen3-VL分片safetensors索引、模块—参数目录、shape/dtype/绑定关系；保留中文；按需读取与数据权限适配 | AI能自己计算分数、排序、选标量/列/头/模块；不要求系统提供一个固定“选神经元”算法 |
| **测内部计算、验证解释** | 旧数学forward有teacher-forced、hidden_states、MLP输入、注意力读数 | VLM多模态teacher-forced/输出评分及按需测量：视觉编码、融合、解码层；图像patch/token、文本token、生成位置对齐；临时干预清理和记录 | 返回的张量能对应准确模块/输入位置；不默默把所有测量映射到最后提示token或仅文本MLP。临时激活干预与静态补丁分开 |
| **自己计算并提交修改** | kernel的save_edit/drop_edit与观察者snapshot：形状/有限数/实际dtype变化/hash校验 | 分片权重读写；通用参数修改；绑定权重一致性；候选父ID、相对W0有效变化、临时/最终标量上限；原版只读；按新合同更新旧禁改列表 | 同预算下可修改不同层和模块，计算公式由AI代码产生；越界/非法值拒绝，不把不熟悉的算子拒绝为“非既定配方” |
| **测新补丁是否真的更好** | v5真实图文生成路径；B/C逐题评分；旧数学有原版/编辑版配对比较 | `evaluate(candidate_id, allowed_items, mode)` 接口；原版/父候选/新候选对齐；跨候选修对/改错及保护项；正式开发全包与局部诊断分开 | 回传实际回答和成对变化，不只总分；输入/模板/评分保持匹配；局部挑题收益不能直接更新最佳候选 |
| **保留、回退、换解释、继续** | 旧kernel可撤销单张量；broker有动作ID、持久日志和不确定请求核账 | 完整候选快照/父关系及原版重建；清理全部hook/cache；当前试验与最佳候选分离；统一动作计账 | 失败后真正回到指定hash；重复请求不重复执行；下一轮可以改支持或方法，不能仅遍历预写增益 |
| **冻结并独立确认** | 旧snapshot有数值/hash记录；已有D/H身份意识与独立来源分组 | 新确认集及只对观察者开放的执行入口；冻结所有比较配置；补丁重载与无hook普通推理；搜索费用/测试预算和保护界限 | AI不能读取封存题/答案或终验反馈再选补丁；冻结产物独立可重建，不依赖研究者会话 |

其中内部求导/归因属于方案允许但当前未提供的可选诊断能力：旧kernel与Reader默认关闭梯度。实现时应明确区分“请求一次受计账诊断求导”和“训练更新目标权重”，不能因不支持求导就声称这类诊断已开放，也不必把所有高级诊断实现完才接通基本闭环。

##### 4. 不能直接复用的具体假设

1. **权重文件格式不匹配。** [旧kernel](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-process-reproduction-v1-2026-11-03/author-code-reuse-r1/adapter/sandbox_kernel.py)L24/33和[快照器](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-process-reproduction-v1-2026-11-03/snapshot_edits.py)L33写死单个`model.safetensors`；当前VLM runner L134读取`model.safetensors.index.json`。必须支持分片映射，不是改一下模型名称就好。
2. **模型与测量结构不匹配。** [旧forward Reader](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-process-reproduction-v1-2026-11-03/engineering-r2/forward_service.py)L245–287用纯文本AutoModelForCausalLM和Qwen3.5全注意力/GDN约定；当前Qwen3-VL输入带图像像素及网格信息。视觉、融合及其进入解码计算的具体位置须按固定版本源码映射，不能沿用旧文本层编号猜测；本次未据模型实例完成该模块映射。
3. **原作者历史限制不等于当前合同。** 旧kernel/snapshot固定排除最终norm、embedding/head，并禁止整张量常数缩放；新方案允许有依据的其他参数编辑。迁移须按当前合同处理：统一缩放整个网络/只改温度仍不算局部修复，但不能用旧过滤器悄悄缩窄已允许范围。实际稀疏总量上限在旧snapshot中只有计数，没有当前方案所需的强制上限。
4. **研究者看不到图像。** 数学controller L46–48禁用原生view_image等工具，editor_turn只通过文本stdin送提示；CPU kernel也只返回文本，L104还将非ASCII替换。不能以“目标VLM能看图”代替“研究者能看开发证据”。需要带权限和费用记录的开发图像入口，不开放整仓库/封存图像。
5. **双卡及预算规则不匹配。** [旧broker](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-process-reproduction-v1-2026-11-03/author-code-reuse-r1/adapter/broker.py)L125–145为`both`寻找两张卡；当前单卡串行安排不能照搬。比较可串行或复用严格同协议的已保存基线，但缓存身份必须绑定输入、模型、处理器和生成配置。搜索还需累计样本、实际文本/视觉token、失败、重载、CPU和研究者成本；原筛查12小时不包含这批搜索。
6. **数据隔离尚未接入AI工具。** 当前D/H文件和标签都在研究目录；runner的H登记门只控制运行顺序，不是研究者文件权限。将来kernel/图像接口只能看到允许的开发资料；新确认集及答案由观察者持有，不能把整个仓库挂进去。
7. **旧暂停记录必须保留。** `author-code-reuse-r1/PAUSED_BY_USER.json`仍写明数学含验收挂起、编程退出队列。复用源码不意味着重启旧任务；本次也没有清除暂停文件或调用其服务。

##### 5. 最小补齐路径与验收要求

这是待办顺序，不是本次实施或运行指令。沿用一个新版本VLM工作目录；不修改历史数学/编程运行、也不破坏v5已验收筛查入口。

1. **先把开发证据与动作接口接起来。** 复用controller/broker的会话、动作ID和原始记录；增加允许开发组的图文访问，返回未经筛选的逐题反馈。受计账的“分析代码＋测量/评价请求”足够，不先造一个固定算法菜单。
2. **接通权重工作区和VLM测量/评价。** 适配分片、实际模块和图像/文本位置；接收AI计算的候选；复用v5处理器/生成与B/C评分，但候选运行使用新身份和新预算，不能绕过v5的“阶段不可重跑”保护。
3. **补齐事务与隔离。** 候选验证、提交/回滚、基线重建、实际BF16改动计数、计账、受控确认集权限。旧单矩阵保存只是部件，不是整个候选的原子提交。
4. **先做无真实模型的协议验收，再分别安排真实工程验收与研究。** 合成工具结果应驱动测试会话走两条不同动作路径；证明接口可接受不同模块、任意合法代码而不是固定排名。拒绝未知/越界参数、超预算、终验数据访问；验证回滚、hash、重复动作不重放、错误不当答错。此类模拟证明接线，不证明AI研究能力。真实小规模VLM前向/编辑/回滚/重载及真实研究者工具往返必须之后明确安排，不能用模拟代替。

不需要现在先实现全网穷举、固定两层定位器或所有探针算法。要补的是“让AI提出的方法能被执行、测量并可靠反馈”的能力。高级测量可按真实诊断需要增加，未支持范围明列，不能把工具缺口当方法失败。

S0原版64条P0仍是筛查的工程缺口，**不是修补闭环的全部缺口**。即使P0及B/C筛查全部通过，也只拿到了开发行为；不会自动获得修改/测试能力。修补前另缺研究者版本、搜索数值预算、保护界限、新确认数据及比较方法配置。当前无法根据静态文件保证这些工作的GPU耗时或搜索成功率，不报虚假的“完成百分比”。

##### 6. 本次自查与结论边界

- 跟踪了实际调用链，不用文件名“editor/diagnosis”推断自主能力；特别区分开放数学controller、固定WCP标注器与作者重放器。
- 检查了原版加载、候选接口、分片、测量范围、图像反馈、Unicode、停止/预算及数据权限，避免只移除“两层”文字就宣布完成。
- 旧4轮/1前向工程回执只证明旧链路历史集成；v5已有6项合成测试只证明进程/记账，不是VLM编辑验收。没有重新执行这些测试或据此声明实时可用。
- 当前方案已经允许自由诊断和选点，本次不重新改任务或阈值；清单中的接口与验收是实现缺口，不提供人类预定的科学配方。
- 本轮没有新增实验设计，沿用v2的C01–C14自查；复核与本次最相关的C03资产、C05操作、C11工程/科学失败、C12成本、C13身份，均按“静态能力／历史回执／待实现／待运行”分开报告。
- 审计只新增本文、来源哈希和目录入口。没有修改研究代码、数据、权重、环境、暂停状态或任何运行配置。

**最终判断：已有支撑部件，尚无可运行的VLM自主修补闭环。优先复用开放数学控制器与VLM原版后端，补齐图文证据、内部测量、通用编辑及候选评价之间的连接；不要移植WCP固定选点配方。**

---

### 原件 5：WSP-VLM v6：开放研究工具与反馈闭环

原路径：`experiments/wsp-vlm-open-repair-v6-2026-11-05/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/README.zh-CN.md) · [单独阅读副本](../library/93f100a6df1707b3.md)；SHA-256：`93f100a6df1707b3efeb221432c1cbb4a913d2a676bddb59182f3d1999b58a7a`。

---

#### WSP-VLM v6：开放研究工具与反馈闭环

##### Material Passport

- 日期：2026-11-05。身份：工具实现、离线工程验收；不是模型实验结果。
- 用户授权：按工具缺口清单补代码、离线验收、自查、提交GitHub；不加载真实模型或处理器、不运行推理、研究者AI或GPU实验。
- 依据：[总方案v2](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-vlm-ai-repair-plan-v2-2026-11-05.zh-CN.md)、[工具审计](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-vlm-ai-tools-audit-2026-11-05.zh-CN.md)。任务、B146/C160、S0统计和预算没有改变。本目录另建v6，历史数学/WCP/v5源码、暂停记录和回执未修改。
- 技能：Ponytail最小复用；Academic Research Suite验收口径；[C01–C14自查](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/SELF_CHECK.zh-CN.md)为同一助手自查，不是独立审查。

##### 本次完成了什么

**已有可离线验证的开放动作闭环；真实VLM修补闭环仍待工程验收。** 不再只有“原版运行器＋文字上的开放诊断”，也没有移植WCP固定两层/8或32通道/列增益配方。

研究者查看开发成功/失败及图片 → 自行提出解释 → 写Python读取/分析参数或请求内部测量 → 自行选择位置和计算新值 → 观察者提交候选 → 原版/父候选/新候选在同包输入上评价 → 原始回答、修对/改错和费用返回研究者 → 继续、回退、改变方法或停止。

**WSP出现在“AI用反馈决定怎样直接改变训练后模型的少量现有权重”这一环节。** 工具提供读写、测量、预算和公平评分；不负责预先决定神经元排名、层数、修改方向或搜索轮数。临时激活干预仅提供诊断信息，不能作为静态补丁交付。

| 文件 | 实现与复用 |
|---|---|
| [controller.py](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/controller.py) | 直接复用旧数学controller的动作解析器；改造持续会话和工具反馈循环。接受AI写的Python/forward，不强制50次；允许无补丁停止。图像用经哈希验证的附件接入。研究者模型/CLI版本待指定 |
| [kernel.py](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/kernel.py) | 沿用数学持久Python命名空间、load/save_edit等接口，改为NumPy、UTF-8、分片权重及通用参数。真实执行仅允许Linux bubblewrap；无不隔离的生产回退 |
| [weights.py](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/weights.py) | 分片safetensors目录/按需读取；绑定参数核验；任意合法浮点参数编辑；候选父关系、原子提交、hash、相对W0的实际BF16支持数与范数、最终稀疏上限 |
| [backend.py](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/backend.py) | 按v5图文输入和greedy128协议准备延迟加载后端。运行时枚举真实模块，不写死层；支持任意已命名模块的输入、kwargs、输出测量、teacher-forced分数和临时坐标干预；异常清理hook、恢复原版参数 |
| [evidence.py](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/evidence.py) | D专用图文证据导出、按ID看原图/预览、严格B/C评分直接复用旧代码。保持目标模型输入只有文字与图；标签仅给研究者/评分器 |
| [service.py](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/service.py) | 复用数学broker的动作身份和未完成请求不重放原则；跨候选原始回答与配对反馈、完整开发集门槛、保护项、缓存身份、失败计账、候选选择/冻结 |
| [confirmation.py](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/confirmation.py) | 观察者专用终验函数；新来源组及图片哈希排重、独立性审核凭据、新输出目录、全新后端。无AI修改/回传接口；不编造新终验数据或统计阈值 |
| [live.py](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/live.py) | 接线入口与整体硬超时；默认只检查配置。自主搜索须单独授权、冻结数值合同并有真实工程验收记录。工程/终验不从此入口启动自主搜索 |
| [prepare_model_view.py](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/prepare_model_view.py) | 从已下载、已核验快照生成无符号链接的模型视图，仅字节核验/硬链接或复制；避免隔离环境挂载整个HF缓存。此次未执行真实模型视图准备 |
| [reuse.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/reuse.json) | 所有复用入口和评分依赖hash；源码漂移即拒绝。没有导入会在模块顶层加载模型的旧kernel/broker |

`catalog/load/save_edit`的范围不限定MLP、注意力或视觉模块。低秩也按实际变化标量计数；提交不同绑定别名的冲突值会拒绝。最终规范仍是同架构静态权重，不改变推理提示或评分规则。

##### 数据准备实际状态

已用现有本地原图及已验收的处理器预览导出以下开发包，并逐文件核对哈希。没有重新加载处理器、生成新预览或打开H输出。

| 包 | 来源组 | 输入 | 内容哈希去重后的图片文件（原图＋预览） |
|---|---:|---:|---:|
| B_D | 58 | 464 | 89 |
| C_D | 64 | 2,560 | 256 |

证据：[导出回执](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/audit/development_export.json)。包位于`external/wsp-vlm-open-repair-v6-2026-11-05/{B_D,C_D}`，不把重复图片加入Git；导出器、冻结上游资产和hash可重建。两包均没有原版回答；这是真实缺项，不用合成结果填入。B146/C160是全筛查组数，上表只是D的58/64组，没有削减正式样本。

任何未来已见H若转为修补开发材料，都需单独导出、登记“已见”；当前导出器只接受D。现有H不会自动成为补丁终验集。

##### 离线验收及其边界

[测试代码](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/test_offline.py)、[逐项日志](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/audit/offline_tests.log)、[验收回执](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/audit/offline_receipt.json)、[两条合成闭环轨迹](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/audit/synthetic_traces.json)。

验收包含：两分片读取；跨视觉/注意力/MLP的修改；绑定别名冲突；F32源值在BF16运行精度下重新计数；溢出/未知参数/形状/预算拒绝；父候选及回滚；重复请求幂等和未完成请求阻断；修对/改错、格式与保护损伤；局部挑题不能升为最佳；缓存篡改；封存ID/路径拒绝；测量部分成功留档；失败Python候选留档；异常权重回滚和hook清理；图像附件；中文与变量持久性；终验组/图片冲突和重复目录拒绝；无补丁提前结束。

两条合成轨迹仅改变测量反馈，**测试脚本**分别选中视觉参数和注意力参数，均走完提交→评价→保留→冻结。它证明接线没有把选择锁死，不证明真正的研究者AI会作正确诊断。测试中的固定脚本只存在于`test_offline.py`，不会用于实际研究。

测试使用手工编码的2×4合成张量和假后端。真实模型权重反序列化、模型/处理器加载、研究者调用、目标推理、GPU运行均为0；测试进程未导入torch/transformers/safetensors/huggingface_hub。还只执行了本地CLI的`--help`以核对图像附件参数，没有调用模型。

可重做的离线命令（无模型）：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 experiments/wsp-vlm-open-repair-v6-2026-11-05/test_offline.py
PYTHONDONTWRITEBYTECODE=1 python3 experiments/wsp-vlm-open-repair-v6-2026-11-05/live.py --config experiments/wsp-vlm-open-repair-v6-2026-11-05/config.template.json
```

模板当前`mode=offline, authorized=false`，数值预算为null；检查会报告执行关闭。离线测试自己的小预算是测试夹具，不是研究额度。

##### 仍缺什么

1. **真实行为证据。** S0的64条P0及B/C筛查没有执行，开发回答为空；没有已确认的失败机制或修补对象。当前代码不绕过原筛查P0门。
2. **真实机器上的工程验收。** Linux bubblewrap挂载/网络/GPU/封存资料隔离、所选研究者CLI的图像与会话往返、固定Qwen3-VL的模块/绑定映射、激活位置/teacher-forced评分、原版输入一致性、补丁回滚及重载数值一致性都未实测。只用Python替身验证过控制流和异常清理；不能据此宣称真实钩子数值正确。
3. **运行配置与费用。** 指定研究者模型/CLI hash、模型视图及完整文件hash、核验实际绑定别名；准备独立NumPy CPU环境（kernel拒绝含torch/transformers/JAX/TensorFlow的环境），观察者后端另用已固定GPU环境；填入并冻结搜索调用/样本/文本与视觉token/时间/临时与最终支持数/保护界限等。研究者CLI usage不是账单，需要外部账户费用上限及凭据；代码记录逐次usage和保守费用预留，不能伪称单靠CLI保证美元硬上限。
4. **独立确认材料和比较方法。** 新来源组隔离数据、已见组与图片登记、人工/数据来源独立性审核、效果/保护界限和功效、近邻编辑/适配基线仍未准备。终验函数只负责严格执行，不替代这些研究决定。哈希排重不能识别所有重压缩图/同物体近重复，仍需要来源审计。
5. **非基本闭环所需的可选测量。** 当前提供模块张量、分数和坐标干预；没有实现任意诊断求导、专门的注意力概率提取或模型专属视觉patch语义映射。这些是明确工具边界，不能用工具不支持来判WSP失败。按真实诊断需要补充，不预先穷举所有探针。

当前候选选择在完整开发包上使用主条件联合正确率、保护条件、格式/截断界限，平分优先更少标量；这是实现的开发选择规则，不是独立显著性判据。目标/保护数值尚空，不允许实际搜索。一次调用的token先按输入上限＋128保守预留，失败不退回；同时另报实际token和其中视觉token，不把视觉token重复相加。整体硬墙钟覆盖模型加载、研究者思考和计算；CPU工具计时为墙钟近似，尚未承诺精细GPU活跃时间归因。

闭环遇到未知完成状态会停止并保留现场，不自动重放；当前没有自动跨进程恢复研究者/CPU变量的功能。候选和工具结果可重建，但恢复需要观察者显式核账。有限输出上限和张量元素上限用于工程资源，不用于限定层/神经元选择。

搜索入口会校验真实工程验收回执的hash/各项检查，以及原筛查P0接受记录和B/C D/H完整输出；合成验收回执不能解锁。隔离和禁装模型框架减少绕过服务的路径，但不声称静态代码能证明任意NumPy程序没有实现训练/额外前向；非梯度、全部模型计算计账仍是公开研究合同，必须保留并审阅AI提交代码。

下一步应先完成授权范围内的真实工程验收及S0行为采集，再冻结搜索数值合同。此交付不启动它们，也不承诺一定能得到有效补丁。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [audit/offline_receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/audit/offline_receipt.json) | {"status": "passed"} | {} |

## 全部原始资产入口

本目录在固定提交下共有22个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/136-wsp-vlm-open-repair-v6-2026-11-05.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05)。未复制模型权重、环境或凭据。
