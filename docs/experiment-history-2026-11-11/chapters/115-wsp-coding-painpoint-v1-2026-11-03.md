# 115．WCP编程数据与编译干预验收

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-03；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

冻结MBPP开发/验证与HumanEval+终验、隔离代码执行、检查编译权重干预及阶段调度。

**实际过程、结果与后来更正**

CPU隔离/评分通过，两模型合成短样例验收；runtime与compiled BF16等价检查超旧阈值，0.8B最大0.0755806、4B0.1193173，用户选择编译针而非调高阈值。后续正式诊断未完成，不能把工程报告当编程收益。

**来源身份**：`wsp-coding-painpoint-v1-2026-11-03`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：WSP × Acupuncture：0.8B / 4B 编程痛点诊断与稀疏干预方案

原路径：`docs/wsp-coding-painpoint-v1-2026-11-03/PLAN.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-coding-painpoint-v1-2026-11-03/PLAN.zh-CN.md) · [单独阅读副本](../library/fe6c1a98c4c30821.md)；SHA-256：`fe6c1a98c4c30821504a83f3e3bd95f699ff6eec1701c068430fad8c6165b249`。

---

#### WSP × Acupuncture：0.8B / 4B 编程痛点诊断与稀疏干预方案

##### Material Passport

- 编号：WCP-01 v1，2026-11-03，工程修订 r2；Origin Skill: academic-research-suite / experiment-agent；Mode: plan。
- r2 用户明确选择：保留 BF16 编译权重干预，明确不等同运行时针。0.8B 合成验收的 +0.5 增益使两实现最大 token log-prob 差为 0.0755806，超过旧 0.05 门槛；失败原件保留，未提高该阈值。修订只改变主操作的身份与相应工程门槛，不改变数据、选点、候选、样本数或正式运行授权。
- 状态：**逻辑设计自查通过；已授权并实施配套工程验收；正式搜索未授权、未启动。** 工程结果见 [验收报告](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/REPORT.zh-CN.md)，科学效果仍 UNVERIFIED。
- 用户当前授权：补齐数据、评分器、隔离执行、干预接口及短合成验收，并复核 ETA/磁盘。数学 50-pass 配置不变；本方案不是启动命令。
- 配套：[自查](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-coding-painpoint-v1-2026-11-03/SELF_CHECK.zh-CN.md)｜[数量与预算](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-coding-painpoint-v1-2026-11-03/BUDGET.json)。本轮不创建可启动配置。

##### 1. 主问题、设计卡和结论边界

主问题：能否从模型自身的编程失败中发现一个重要、可干预的瓶颈，并通过稀疏干预提高独立任务上的完整代码正确率？这是 WSP 过程复现的编程扩展、Acupuncture 稳定控制方向的能力修复检验，不替代既有缓存机制主线。

本轮只研究 **Python 纯函数/小函数生成，一次生成、不接收执行反馈、不联网、不使用仓库工具**。不是 SWE-bench、项目级开发、交互调试或整体编程能力的完备测量。测试反馈给研究编辑器，不能在同一答题尝试中反馈给被测模型。以后研究调试能力须另立协议。

设计卡：

|项|本轮约定|
|---|---|
|新增认识|两个模型各自是否有一个稳定的主要失败模式；由自己的诊断选出的通道增益干预，能否在独立编程题上产生净收益。|
|依据|作者 WSP 展示从失败轨迹到编辑的可行先例；本项目前向/编辑器已有工程验收；二者都没有证明本模型的编程瓶颈已被找到。|
|不利证据|作者的非循环 Gemma 跟进收益有限；既有 Acupuncture 有停止、失真和剂量副作用。少通道不是小扰动；失败可能分布式、知识不足或没有稳定可修复点。|
|操作|在原始模型一个 MLP 的 down_proj 输入处，对选中的 8 或 32 个通道施加固定乘性增益；覆盖全部 prompt 和生成位置。具体层/通道只从该模型开发数据选择。|
|固定/响应|固定模型版本、题目、种子、提示、采样、预算、评分器；激活修改后全部后续网络、缓存和生成自然响应。无供体替换、无缓存钉住。|
|估计对象|完整生成下干预的总效果；不是原生路径份额、信息存量或唯一根因。|
|退出|没有足够可诊断的失败/配对、开发验证不改善、资源/工程失败，均按下文停止；不自动换题、扩层、加剂量或追加 50 pass。|

**成功也只能说明这两个模型在规定任务、干预族和预算下的结果；不能据此声称通用全局最优诊断器。** 找不到有效针，也不推出 WSP 或所有稀疏修复都不可能。

##### 2. 来源与已有资产

固定作者来源：`RikiyaT/lm_understand-logs@4d09ba6d6a7e891dd8063974dfe81b3d78e3494f`，[实验说明](https://github.com/RikiyaT/lm_understand-logs/blob/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/exp8_math/README.md)。本轮继承“观察→提出假设→编辑/干预→前向检验→保留失败”的逻辑；**不向编程编辑器提供数学最终补丁、层/通道、重复方向、搜索 notes 或另一个模型的发现**。观察者已知作者结果，不称整个研究者群体盲法。

模型版本与现有数学线一致：

|项目|0.8B|4B|
|---|---|---|
|原始发行模型|Qwen/Qwen3.5-0.8B|Qwen/Qwen3.5-4B|
|固定 revision|2fc06364715b967f1860aea9cf38778875588b17|851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a|
|decoder 层数|24，索引 0–23|32，索引 0–31|
|当前文本资产|external/wsp/text-Qwen3.5-0.8B|external/wsp/text-Qwen3.5-4B-r2|
|搜索身份|新建独立 gpt-6-astra/max 会话|另一个新建独立 gpt-6-astra/max 会话|
|科学假设|不预设循环为主因|不从 0.8B 继承主因或针眼|

从未编辑的发行权重开始；“原始”不等于随机初始化或未经发行方训练。文本导出、tokenizer 和环境指纹复用既有收据，运行前核身份，不重新下载模型。

工程基线：`experiments/wsp-process-reproduction-v1-2026-11-03/engineering-r2/` 的 [验收合同](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-process-reproduction-v1-2026-11-03/engineering-r2/ACCEPTANCE.zh-CN.md)、`receipts/engineering-r2-{0p8b,4b}-r1-receipt.json`、编辑器集成收据与 [资源核算](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-process-reproduction-v1-2026-11-03/engineering-r2/STARTUP.zh-CN.md)。这些证明既列接口可用，不证明编程评分、长序列干预或编程增益已验收。

任务来源：

- 开发：Google MBPP，固定 `google-research/google-research@f46ca8374b4cddef97ca4208ad986049d74d296a`，`mbpp/mbpp.jsonl`。[原作者划分](https://github.com/google-research/google-research/blob/f46ca8374b4cddef97ca4208ad986049d74d296a/mbpp/README.md)：601–974 为训练题，11–510 为测试题。我们只从训练题选择开发数据。
- 终验：HumanEval+ **完整 v0.1.10**，计划 164 题；不用 Mini/NoExtreme。评分代码固定 `evalplus/evalplus@26d6d00bb1fd0fa37f39c99d5290da67891d1c5e`，其 [loader](https://github.com/evalplus/evalplus/blob/26d6d00bb1fd0fa37f39c99d5290da67891d1c5e/evalplus/data/humaneval.py) 默认该版本；资源 URL 为 `https://github.com/evalplus/humanevalplus_release/releases/download/v0.1.10/HumanEvalPlus.jsonl.gz`。下载后记录实际 SHA256、条数和测试数，不以 URL 代替哈希。
- EvalPlus 评分器复用其比较规则与参考耗时逻辑，不另造宽松“正确”定义。公开数据可能在预训练中出现，留出指**本次编辑选择未见**，不称预训练无污染。

原方案交付只核资料；后续工程授权允许下载固定数据并在隔离环境执行参考程序，不生成研究题模型回答。无该任务的新旧科学结果可供直接复算；新增模型测量确有必要。

##### 3. 数据、提示和信息隔离

工程准备先冻结四个互斥面板，两模型使用相同题目，所有结果和候选相互隔离：

|面板|数量|用途与可见性|
|---|---:|---|
|D 诊断集|128 道 MBPP train|每题 2 个种子；编辑器可见题目、开发测试、完整回答与反馈，用于失败分类、选点和剂量筛选。|
|S 筛选子集|D 中预先抽定 32 道|固定子集，不按失败挑题；12 个候选各 1 个种子；原版复用 D 同种子。|
|V 开发验证集|64 道 MBPP train，与 D 分离|候选冻结后一次性开封；六臂比较。只作去留判断，不依据 V 回头改针或换候选。|
|T 外部终验集|HumanEval+ 全部 164 道|编辑器不能访问题目、解答、测试或分数；冻结针和候选选择过程后，由独立权限的评分进程执行。|
|M 数学副作用哨兵|64 道 GSM8K test|仅 observer 在最终阶段比较原版/针；不进入编程或数学编辑器上下文。不是完整数学终验。|

抽样：规范化 task_id 后按 `SHA256("WCP01-v1|"+dataset+"|"+task_id)` 排序；MBPP 合格池前 128 为 D、随后 64 为 V，D 再按 `WCP01-S|id` 排序取 32。M 取该规则的前 64。种子由任务 ID 与 sample index 0/1 确定，跨臂相同、跨模型规则相同。相同种子是配对组织方式，不保证分歧后同一语义随机数。

合格池在首次生成前完成 CPU QA：参考代码能通过给定测试；接口/规范明确；依赖在冻结环境内。仅看到源题与参考，不看模型表现。规范冲突记录排除理由，不从参考程序盲目扩出“真值”。MBPP 原始测试较弱，D/V 的“通过”只是开发标签；入选故障类别须由失败输入、规范和代码逐条核对，不能仅听 Astra 解释。

用规范化文本、去标识符 AST 和 token 相似度做 D/V/T 去重审计；疑似同算法模板人工核对，优先从开发池排除并按固定顺序补齐，保持 T 不删题。只记录去重映射，T 内容不交给编辑器；同家族留在同一开发分区。如不足 192 道合格开发题，或 T 不是预期版本/数量，停在数据工程阶段修订并重查，禁止静默换集。测试覆盖不足和预训练污染保留为外部效度限制。

统一任务提示：提供自然语言题意、明确函数签名和公开示例，要求返回一个完整 Python 函数/模块、保留函数名，以一个 python 代码块交付；不附参考解答或隐藏测试。MBPP 的函数接口由原始规范/测试提取并在模型运行前审核。HumanEval 仅把其公开 prompt 中签名、docstring 和既有 import 作为任务输入。

主协议：thinking on，temperature=0.6、top_p=0.95、top_k=20、**presence_penalty=0**，每次最多 **16,384 新 tokens**，包括思考和代码。该设置为本次编程扩展，**不是复刻作者数学的 32k/penalty=1.5 协议**。改为零重复惩罚避免预先惩罚代码正常复用；本轮不搜索解码参数。32k 不能从未授权的后续尝试偷偷补跑。

代码抽取冻结：仅处理最后一个 `</think>` 后的答案；如果 thinking 未闭合，标记未交付，不从思考文本找可用代码。取最后一个 python/无语言标记 fenced block；没有 fence 时将整个答案作为候选代码；不修语法、不重命名函数、不拼接多个候选、不调用模型补全。保留原始回答和抽取产物。CPU fixtures 覆盖上述规则，所有臂完全相同。

##### 4. 两个模型分别怎样找主要痛点

0.8B 先做；随后 4B 独立重复同一规则与同一任务划分。只传工程修复与共享资源规则，不传失败排名、选点、方向、剂量、测试表现或研究 notes。4B 的更大层数只改变合法索引和资源额度，不增加搜索候选数。0.8B 科学阴性不取消 4B；共用评分/工程错误则先修复，不继续制造不可比数据。

###### A：先形成失败图谱，而不是先找神经元

D 的 256 条原版回答记录：完整文本/token、抽取代码、是否截止、语法/导入异常、每个测试结果、超时/内存、首个可复现失败输入、总长度和执行时间。

机器证据先分类为：未完成交付、语法/接口失败、运行时异常、执行超时、测试错误、通过。语义二级标签允许多标签：约束/边界遗漏、变量或状态更新错误、算法选择错误、推理循环、其他/无法判定。标签附具体输入/代码位置/证据；“循环”不能只用输出长判定，“超时”不能直接命名算法知识不足。LLM 标签和测试事实分别存储。

按**独立题目**统计类别占比，并报告全部类别与 unknown。最多审查占比最高的两个语义类别，选择其中占比最高且满足下列诊断条件的一个作为本模型目标：涉及至少 12 道题，并有至少 8 道“同题两个样本一个通过、另一个出现目标失败”的配对。两类都不满足就报告本轮不可诊断并停止选针；不改题/增加采样寻找成功故事。阈值用于最低证据量与成本控制，不是显著性标准。

这选出的是**该面板里优先检验的痛点**，不是已证明的全局最大损失来源。同题有成功样本提示模型偶尔能完成，仍不证明两条轨迹只差一个故障因素。

###### B：从配对轨迹提出位置候选

最多取 32 对符合条件的原生成功/失败轨迹，按固定哈希顺序，原样 teacher-force 重读。循环/未交付目标取思考末尾 128 tokens；代码语义目标取最终代码前 256 tokens。两成员使用相同阶段规则；不足取实际长度；不能为了分数把窗口移到最有利位置。无对应阶段的配对剔除并记录；剩余不足 8 对停止定位。这是有限窗口搜索，阴性不能否定其他时段。

各层采集 down_proj 输入通道在窗口内的均值、RMS，按题先求成功/失败差，再跨题汇总。通道排序使用标准化差值绝对值 `abs(mean_pair_difference)/(pooled_RMS+1e-6)`；每层前 8 通道分数均值决定层排名，平分按层号/通道号。选择前两层，各取 top-8/top-32，组成 **4 个固定支持集合**。记录正负方向，不把大激活差称因果。

全层仅保存聚合统计；选中层保留有限 token 窗口，原始生成轨迹完整保留。TF 计算总量上限 2,000,000 输入 tokens/模型（包含验收、定位和干预读数），不能用截掉 prompt 的方式伪造完整历史。实现应按 batch 流式统计，现有全张量返回接口需适配。

##### 5. 怎样扎针、怎样验证

###### 5.1 第一轮只允许一种明确、可验收的操作

精确算术下的动机是在一个选定 MLP 的 `down_proj` 输入处，选中集合 J：

`a'_j(t) = (1 + λ) a_j(t), j∈J`；其余激活不动。

r2 实际操作以 §5.2 的 BF16 编译列增益为准，不把上式当成 BF16 运行时等价保证；设计卡中的“通道增益”也按此定义解释。

每个候选只有一层、8 或 32 个通道；全部 prefill 和 decode 位置均执行，后续状态自然响应。不是固定值覆盖，不是加性针，不使用动态故障检测器，不改 embedding/norm/head，不做梯度训练。先筛四组支持 × λ=−0.5/+0.5，共 8 候选；S 上按净正确数、再按较少通道、再层号/负号优先选两个不同支持集合，对其补测 λ=−1/+1，新增 4 候选。合计最多 12；无有效支持则少跑，不能补充其他编辑形式。

最终在 S 上从全部已测候选中选一针：正确率最高，平分按通道数、|λ|、层号、负号优先。不依据“症状变少但答错更多”选针。候选和症状预测、失败标签规则、随机对照在打开 V 前冻结。

这一族是为了把“找痛点→稀疏干预”做成有限可证伪检验，**不是穷尽 WSP 的权重编程能力**。若失败，不自动退回作者数学方向投影补丁。

###### 5.2 可复用静态加载路径，但不声称任意动态针都等价

该固定乘性针在精确算术下可编译为选中 down_proj 列 `W'[:,J]=(1+λ)W[:,J]`，其他列不变；因为 `W(Da)=(WD)a`，在每个位置都施加时可复用 vLLM 权重编辑生成。此等价只针对本操作，不适用于时间窗针、加性针、条件触发或任意 WSP 投影编辑。

实际主终点定义为 **BF16 编译列增益干预**：`W'[:,J]=BF16(float32(W[:,J])*(1+λ))`。r2 验收要求零增益生成与原版一致，保存/重载后的目标矩阵逐元素等于该公式，其余所有模型张量逐元素不变；快照、构建文件与生成调用身份可追溯。FP32 局部等式仅作基础实现检查。

运行时激活增益只作诊断，不是主实验同义实现。原 BF16 等价门槛未通过的记录仍保留，后续对照继续报告实际误差而不以它决定编译操作是否正确；不能把运行时干预的读数直接当作编译干预的因果证据。解释选点作用时应在编译权重条件下重读。本修订得到用户明确选择，非事后提高容差制造通过。

###### 5.3 V：一针、六臂、一次性去留

64 题 × 2 种子 × 6 臂 = **768 回答**：原版、选中针、同支持反号针、三个同层同通道数随机支持针。随机支持排除目标集合，以固定种子生成，不用表现选随机针；在 D 原版激活上校准其系数，使支路扰动 RMS 与目标针相差 ≤10%，不匹配行为效果。如果所需 |λ|>1 或校准失败，标记随机对照无效并停止进入终验，不不断重抽直到有利。保存固定 λ 与实际逐 token 范数，随机不是严格零分布。

进入 T 的条件：选中针比原版至少净多对 4/128 个样本（3.125 个百分点），且高于三个随机针的平均正确率；如果至少 8 道 V 题出现目标症状，冻结标签下目标症状题数也应减少，且不能用更多截断/无代码替代它。少于 8 道则症状迁移证据不足，本轮不作“该痛点稳定修复”结论，但若正确率门槛通过可进入 T 检查一般任务收益。

这些是成本门槛，不是研究阳性判据。反号也改善时，撤回“该符号特异性”解释，不事后改预测；V 不通过即结束本模型分支，保留失败，不换第二候选重用 V。

###### 5.4 T：真正的能力终点与更简单的替代办法

HumanEval+ 164 题 × 2 种子 × 4 臂 = **1,312 回答**：

1. 原版、thinking on。
2. 冻结针、thinking on。
3. 预先编号 random-1 对照、thinking on（不是 V 上最弱/最强的随机针）。
4. 原版、thinking off，其他采样及 token 上限相同，公开提示同义不变。

第四臂用于回答“简单关闭思考是否已能达到同样改善”。它是完整协议替代，不是纯机制对照；报告实际 tokens/时延，不假设等额上限等于等计算消耗。主对比仍是同 thinking 协议针 vs 原版。

主指标为 **HumanEval+ 全部测试通过的 pass@1 估计**：每题两次的平均正确率，再按题平均；不是 pass@2、best-of-2 或只测已生成完整代码的子集。语法错、超时、截断、无代码都计失败。另报 base-tests 与 plus-tests 差异、救回/破坏题数、故障变化、实际输出长度。执行器故障不当模型失败混入完整分母，必须修复或标记实验不完整。

每模型主效果 `Δ = mean_i(mean_s(Yneedle−Yoriginal))`。按题成簇、成对 bootstrap 20,000 次，固定分析种子；两模型各给 97.5% 双侧区间，保守控制两项主对比的多重性。预先定义具有实际意义的提升为 ≥5 个百分点，并且区间下界>0；未达到不能称已证实 boost。164 题仅适于发现较明显效果：按题配对不一致率约 0.2–0.4 的简化单样本近似，80% 检出量级约 11–15 个百分点；双样本相关性未知，不能承诺检出 5pp 小收益，也不能把 328 回答算 328 独立题。

针 vs 随机、针 vs thinking off、症状子组为次要描述比较，给区间但不再筛候选。针仅胜原版却不胜简单协议，应写“修复了该 thinking 设置下的表现，尚无相对简单替代的优势”。针与随机相近则定向诊断优势未证实。

M 哨兵：64 题 × 2 种子 × 2 臂 = 256 回答；原版/针均用既有数学 32,768-token thinking 协议和 math-verify。同题共享种子；只作副作用报警，净下降>5pp 或明显交付崩溃则不推荐默认启用。小面板无下降不等于数学无损，未做全域非劣效证明。

##### 6. 判读、因果措辞和停止

|观察|允许的结论/后续|
|---|---|
|D 没有可诊断配对，或失败很分散|该面板下没有足够证据支持预定稀疏定位；保留痛点图谱并停止，不认定模型毫无知识。|
|V 阴性|这次诊断与乘性通道干预未带来足够开发收益；停止，不能让 T 帮忙选针。|
|症状减少，正确率不升|症状不是足够的能力瓶颈，或干预带来其他损伤；不称 boost。|
|T 正确率升，但冻结症状无支持|有干预总效果；“因修复该痛点而提升”的解释未证实。|
|V 症状与正确率改善，T 主效果成立|支持从该模型开发诊断得到一个可迁移的稀疏修复；症状中介/唯一根因仍未证明。|
|只 0.8B 有效 / 只 4B 有效|报告模型依赖，不称参数规模规律；不互借针眼重试。|
|工程、数据版本或隔离失败|工程阻塞，不当科学阴性；保留原失败，修订后新运行身份。|
|达到预算或 GPU 被占用|暂停并商量；不抢卡、删证据、改短答案限制或自动追加。|

定位仍可能受文本、长度、题目难度与正确性代理的混淆；同题配对及随机/反号比较减少部分替代解释，不能把观察差异自动升级成原因。全位置干预同时改变形成和读取，因此不命名“只修复缓存写入”或“找到原生唯一痛点通道”。

##### 7. 哪些工程复用、哪些缺少

|模块|可复用部分|必须补齐/验收|
|---|---|---|
|模型/环境|现有两套原始文本权重、tokenizer、CUDA兼容环境、已核模型身份|新的任务与编译针绑定快照；不重复下载和重做全套旧验收。|
|生成/TF|vLLM 原版/编辑版配对、固定种子、HF 精确 token 重读|编程提示与评分分支；thinking 开关；流式全层统计和预算；不强行套 mathqa。|
|干预/快照|save_edit、checkpoint 构建/哈希、每步编辑快照|稀疏列增益构造、支持/剂量白名单、runtime hook 对照；检查禁止改动的参数确实未变。|
|编辑器/调度|独立 Astra、持久 CPU kernel、日志、预算、失败/续接|WCP 独立阶段机，D/V/T 权限边界、候选数量/样本/token/资源总账；不能直接复用 50-pass 结束条件。|
|评分|数学 math-verify 仅用于 M|MBPP adapter、固定抽取、EvalPlus 参考验收、代码执行隔离与错误分类。|
|分析|原版/针配对表和证据归档结构|按题聚类统计、失败类别原始证据、随机/反号、成本与数学哨兵报告。|
|断线运行|服务器模型服务、现有日志和 checkpoint|当前 Mac 编辑器/控制器迁到服务器的路径/登录、tmux或等效后台及断线续接验收尚未完成；已有短续接不等于断电无影响。|

执行隔离：生成的代码在单独低权限执行服务中运行，断网、无 GPU、无凭据、无宿主项目/权重/快照写权限，只读题目所需输入与临时工作目录；固定 Python 3.11 环境、4 GB 内存/进程、最多4个CPU worker。EvalPlus 的 Python reliability_guard 不单独充当安全边界。实现时优先复用成熟容器隔离；若服务器环境无法满足，停止讨论替代，不在权重分析 kernel 执行不受信任代码。

CPU 验收：参考解答、已知错误/语法错/死循环、抽取边界、测试泄漏、权限/资源限制、得分聚合、故障不误算模型错误、重复请求不重计；数据 manifest 固定。GPU 验收最多 32 条短合成生成/模型（4 个合成提示×2 种子×原版/零针/−0.5/+0.5 四臂，每条≤128 tokens）及 TF，纳入下节预算；TF 另覆盖 λ=−1/+1，记录 runtime/编译差异；主验收使用 §5.2 的编译公式、全张量身份与零增益生成门槛。覆盖缓存顺序和基线重放，不偷跑研究题。

原设计交付无可执行入口；已授权的工程实现放 `experiments/wsp-coding-painpoint-v1-2026-11-03/`，新记录不覆盖数学实验或既有原始资料。先完成数据/评分/隔离 CPU 工程，再做有授权的短验收；没有必要先把 GPU 常驻等待编辑器或下载。工程 worker 不等于正式阶段调度器。

##### 8. 全流程预算：包括终验，不另藏一笔

每模型最大生成量：D 256 + S 384 + V 768 + T 1,312 + M 256 + 工程 32 = **3,008 条**。其中 2,720 条编程回答每条≤16,384 tokens，256 条数学回答≤32,768，32 条合成回答≤128，合计极端输出上限 **52,957,184 tokens**；TF 总输入≤2,000,000 tokens。未通过门槛的后续阶段不运行。失败与重试也占总 token/时间额度，不在满额之外额外赠送重试。

|预算项|0.8B|4B|
|---|---:|---:|
|阶段 A：短验收＋D诊断及定位上限|0.5 GPUh|1 GPUh|
|阶段 B：S筛选＋V一次性验证上限|1.5 GPUh|4 GPUh|
|阶段 C：T终验＋M哨兵上限|2 GPUh|5 GPUh|
|全流程设备时间停止线|**4 GPUh**|**10 GPUh**|
|新增磁盘工作额度|25 GB|40 GB|
|本模型启动最低空闲空间|75 GB|90 GB|
|运行中共享盘余量|50 GB|50 GB|
|CPU 评分及准备上限|60 core-hours|60 core-hours|
|研究编辑器上限|100 回合、120 Python 调用|相同，独立会话|
|编辑器 token 防护线|累计输入 1.5M、输出 150k|相同；含 reasoning（提供方可见时）|
|运行授权|**false**|**false**|

时间是“预留卡数×服务进程墙钟”，包含模型加载、构建、TF重读、失败和运行内闲置；CPU 评分/编辑器等待时释放模型进程和卡。两卡各跑1小时是2 GPUh，不是1。按阶段和总预算双重停止，不自动借下一阶段额度；如校准显示阶段不足，运行前报告，不能暗改预算。

估算来源：既有短序列吞吐为约 14,045 / 5,124 token/s，52.96M 极端输出对应**仅解码**约 1.05 / 2.87 GPUh；再考虑约 31 个模型配置/阶段装载的摊销、较小 batch、16k 降速、TF、失败。4/10 是第一轮愿意投入的停止线，**不是完成所有任务的性能保证，也不是实际测出的耗时**。阶段 A 用 D 的首个固定批次校准剩余耗时；不额外生造吞吐实验。不能因慢而丢对照、只测顺利题或改变生成上限。

CPU 每份程序使用评分器参考耗时规则，同时独立 supervisor 将一个候选的总执行墙钟限制在60秒；原始参考解答也按该环境预验，参考解答不能完成的题属于工程/协议阻塞。最多 2,720 编程候选理论约45.34 core-hours（单CPU进程上限）；额外参考、fixtures和分析预留到60。逐测试早停/CPU节省不改变判分。四 worker 的最坏墙钟仍可能超过11小时，不能只用 GPUh 承诺当天完成；真实正常程序预计远短于上限，需记录而非预填。

磁盘额度包括完整原始回答/token、所有候选差分/快照/构建记录、有限激活、测试反馈、日志和当前私有编译 checkpoint。复用原始模型；候选不各留完整模型副本。两个模型所有新增证据加共享余量规划 **25+40+50=115 GB**；现有数学新增预算独立，顺序安排不能把同一空闲容量重复承诺。此前清理后的约270 GB只是历史收据，启动时重新检查。不再要求数百GB额外下载；不删除原始实验数据/日志/快照/构建记录。

现金预算：没有当前 H20 单价和 Astra 实际账户计费资料，不能编造人民币额。上限公式为 `14×H20每设备小时单价 + ≤120×CPU每核小时单价 + 编辑器实际费用`，若已有服务器/订阅则区分增量支出和资源机会成本。沿用已授权账户，配额不足暂停，不自动启用付费 API/换模型。CLI 若只给累计token，按会话差分记账，不能累加累计值；无法获得用量时该项验收阻塞，不假称token硬限已生效。

##### 9. 交付与启动门槛

本次交付计划、自查、预算和文档入口，0 GPU、0 新模型调用、0 研究编辑器调用；数学与编程搜索均未启动。

未来启动顺序：数据/版本/去重冻结 → CPU评分和隔离验收 → 服务器常驻/断线恢复准备 → 用户实际执行授权 → 只等空闲卡做短验收 → 0.8B按阶段运行/可能提前停止 → 4B独立运行 → 冻结结果与失败报告。每个步骤保留 receipt，计划通过不代替其中任何步骤。当前“不要启动搜索”覆盖所有诊断研究生成，不把基线偷算成免费准备。

每模型应交付：完整失败图谱、诊断证据卡、所有12个以内候选及失败理由、V去留记录、若进入T则全部原始代码/评分/配对区间、数学哨兵、真实设备/CPU/token/磁盘账单和明确结论边界。即使早停也留下可复用的负面结果，而非空白的“未提升”。

---

### 原件 2：WCP-01 v1 设计自查

原路径：`docs/wsp-coding-painpoint-v1-2026-11-03/SELF_CHECK.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-coding-painpoint-v1-2026-11-03/SELF_CHECK.zh-CN.md) · [单独阅读副本](../library/ad0c6499f9be852f.md)；SHA-256：`ad0c6499f9be852f5c65d89e671bb3c911cb344eae909ca7468bbc60e949d752`。

---

#### WCP-01 v1 设计自查

工程交付复查：四类工程验收与数据冻结结果见[报告](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/REPORT.zh-CN.md)。C12/C13补充：完整研究ETA仍未验证，不把旧批量吞吐或新短合成吞吐当作16k预测；4/10 GPUh仅停止线，工程失败已计账。源题审查先于研究输出，88个相似候选保守隔离、31个规范/参考问题排除；原始失败和选择偏差记录保留。未启动正式搜索，WCP阶段状态机与研究编辑器的阶段权限尚未验收；不能从模块通过跳到全流程无人值守就绪。其余原设计科学判据不变，同一助手自查，不是独立评审。

##### 工程修订 r2（用户明确选择，2026-11-03）

0.8B 原合成验收发现 runtime 激活×1.5 与 BF16 编译列×1.5 的最大 log-prob 差0.0755806，原门槛0.05未通过。已暂停并向用户报告；用户选择“保留编译权重干预，明确不等同运行时针；修订方案与验收”。原失败收据保留，不提高原阈值。

修订后的操作：主实验仅静态 BF16 编译权重增益；零增益、目标列公式逐元素一致、全体其他张量未变、保存重载/生成身份作为验收。Runtime 对照仅诊断，不能把其结果当主操作证据。其余选点、12候选、数据、评分、终验和预算不变。工程验收获得授权，正式搜索仍无授权。

重新审查：C01/C02通过，仍研究诊断选择的稀疏修复；C05/C06/C07通过，主操作与有限精度顺序明确，全部下游自然响应；C08/C09通过，取消数值等价和runtime因果互换的主张，不虚构两者等效；C10/C11通过，代码正确率仍为科学终点，旧工程阴性保留；C03/C04/C12/C13/C14继续通过，新增真实反例、重试消耗计账、数据与选点未看研究结果、无搜索。E03/E19/E23重点复查通过：稀疏不等于小效应、实数恒等式不等于BF16实现一致、工程修订不等于科学阳性。

最强反例：静态权重操作可能成功而运行时针失败。处理：结论只适用于编译权重操作，不能声称验证了原运行时Acupuncture修复；该结果仍可回答WSP式稀疏权重干预能否改善编程。逻辑修订通过（同一助手，非独立审查），新工程通过与否仍看实际收据。以下为初版自查记录，涉及旧数值等价门槛的内容以本段和PLAN §5.2 r2为准。

2026-11-03；规范：[`experiment-design-self-check v1`](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/experiment-design-self-check.zh-CN.md)。审查者为本轮同一助手，**不是独立评审**。审查对象为 [PLAN](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-coding-painpoint-v1-2026-11-03/PLAN.zh-CN.md) 与 [预算](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-coding-painpoint-v1-2026-11-03/BUDGET.json)，不冒充未实现代码的验收。

##### 设计卡与上一版比较

设计卡完整见 PLAN §1；本轮增量是“编程主要失败模式能否指导可迁移的稀疏修复”。保留用户的原始模型、0.8B与4B独立、观察全过程、不抄作者最终补丁、原始证据保留、先不运行的要求。

上一版是数学过程复现与工程 r2，50-pass自由权重编辑、mathqa评分。这里新增一个**独立编程扩展**，不修改数学原合同：Python函数生成、执行评分、数据隔离、一个明确的乘性通道干预族、12候选以内、独立终验和简单协议对照。不是把数学补丁改名，也不把本轮预算加到原50-pass后冒称同一复现。较上一轮口头讨论，从“可能发现各种故障”收敛为有停止条件的实证检验，明确不会在第一轮穷尽所有故障和干预形式。

##### C01–C14

|ID|判定与依据|
|---|---|
|C01|通过。§1保持“找能力瓶颈并稀疏修复”，不是只减少循环、缩短回答或让模型停嘴；仍属能力修复/稳定控制，不替代缓存主线。|
|C02|通过。§4–6得到各模型失败图谱以及固定选针是否迁移的实证；阴性也界定该诊断/干预族的局限，不以代数等式充当发现。|
|C03|通过。§2引用固定作者来源、模型revision、工程收据、MBPP原划分和EvalPlus源码；已有读取/编辑资产可复用，代码评分尚缺。来源数据哈希待数据工程实测，不虚构已冻结。|
|C04|通过。§1/6面对知识不足、分布式故障、作者弱收益跟进、现有针的副作用、文本混淆和预训练污染。只说值得检验，不预设循环主因。|
|C05|通过。§5.1明确down_proj输入、乘性、单层8/32通道、λ集合、全prompt与decode、基于D选择。与加性固定值针分开；无供体或“只操作过去”的歧义。|
|C06|通过。§1/5/6固定题目/种子/协议，所有下游状态自然响应；本轮估计总效果，不声称分离形成/读取。|
|C07|通过。没有拆换k/β等共享变量或补偿；编译等价限于固定全位置对角增益，实际BF16误差另验。不把任意动态针等同权重投影。|
|C08|通过。§5.4/6正确率净提升才叫任务表现改善，症状下降另报；同题关联不能证明唯一病因，反号/随机不构成原生路径证明。|
|C09|通过。§5.3–6区分目标方向有效、一般扰动、简单thinking切换、症状但非能力改善、模型依赖。候选可以同时成立；反号阳性撤回符号特异，不把余项归入预定机制。|
|C10|通过。主终点是全部测试通过的pass@1，含失败和未交付；不以logprob/投影/短输出替代。两样本不算best-of-2，数学哨兵不能证明广义无损。|
|C11|通过。§6/7把评分/数值/资源阻塞与科学阴性分开；V门槛仅决定成本去留，T用预设效果量和区间，不事后降低标准。|
|C12|通过。§7/8复用模型与旧工程，只补新增路径；每一生成数量与TF、加载、CPU评测、失败、终验有上限。无正式50-pass，最多12候选、一个目标、一个终验针；不足即停，不自动扩网格。|
|C13|通过。§3/5要求模型身份、数据manifest、盲于编辑器的T、候选/症状冻结、按题聚类、失败保留。已看V不得改针；两模型隔离；公开基准不称预训练无污染。|
|C14|通过。§6列成功/阴性/异号/不可判，各有撤回或停分支规则；不论结果都不自动导向更大计算。成功至少增加“诊断选择的局部干预可迁移”的有界认识。|

##### E01–E26 历史错误复查

|错误|本次处理|
|---|---|
|E01/E24|目标保持能力瓶颈修复，不要求一次解释全部编程能力，也不退化为停嘴终点。|
|E02|全层只作有限统计选点，层数来自实际模型；不继承数学L15/L19或旧针眼。|
|E03|报告实际支路扰动RMS和逐token分布；8/32坐标不称小剂量，随机支持匹配数与幅度。|
|E04/E19|编译公式和零针等价只作工程检查，主新增证据来自未见任务表现。|
|E05/E06|不操作/拆分共享门控或缓存分量；没有此类路径份额主张，相关机制错误不适用。|
|E07/E14|双向/随机比较只限制替代解释；不声称必要、充分或唯一原生机制。|
|E08|每个臂操作、原始模型、覆盖时段和固定项已列，无含糊供体；这里是全轨迹总效应。|
|E09/E11|内部激活差与行为同步不能证明中介；不从激活投影推知识增减。|
|E10|交付、正确率、截止与症状分别评分；短输出不等于会编程。|
|E12|保留被破坏题、原版正例与随机本身损伤；反号单列，不伪称随机零分布。|
|E13|无答案激活供体注入，不以参考程序的正确性冒充模型原有正确状态。|
|E15|不同模型/题目/阶段的作用不直接拼完整链；D定位、V验证、T迁移的身份分开。|
|E16/E18|阴性可停止；不把剩余原因默认归为某层放大或知识缺失。|
|E17/E26|全位置针会改变形成与读取，不声称撤销先前历史或隔离形成作用。|
|E20|位置、符号、故障类型、解码模式不是互斥解释，允许共同成立。|
|E21|核WSP与执行评测直接来源，本轮不主张领域首创/新颖性已证明。|
|E22|D/S开发、V一次去留、T外部终验；两种子按题聚类；预训练污染未知。|
|E23|本文件同助手自查；设计通过≠工程通过≠授权≠实际结果。|
|E25|删去多语言、项目级开发、交互修复、多个编辑族和无限剂量；全成本含终验，不靠额外矩阵证明认真。|

##### 实质反方检查与修订

1. **全预期结果出现，仍可能只是解除较差解码协议的损伤。** 修订：编程不沿用数学presence=1.5，固定为0；T增加原版thinking off，报告其相对收益和真实tokens。仍无法排除其他未搜索解码方案，因此不声称最优部署策略。
2. **激活差只编码题目、长度或代码内容。** 处理：同题不同原生样本、固定阶段窗口，只作候选排序；只有实际干预终点可支持总效果。目标症状与收益同变仍不足以证明中介，结论已收紧但保留能力修复的实质问题。
3. **开发程序只通过三个弱测试，标签错了。** 处理：CPU先核规范/参考，目标失败需反例证据；T采用完整HumanEval+测试。发现开发标签错误须记录，不能只修有利样本；T阳性前不宣传编程能力提高。
4. **想做runtime针却用静态权重，有限精度下并不等价。** 修订：主终点明确为BF16编译列增益；精确算术等式有适用条件；独立短序列对照有预设门槛，失败停。不能用长生成分歧去“验证完全等价”。
5. **随机干预范数更小，或从随机里挑最差的，让目标显得特别。** 修订：D上按实际写入RMS匹配，V三个预定支持，T固定random-1；失配就阻塞，不重抽到有利。三个随机只是有限对照，无法建立通用随机零分布。
6. **从很多候选挑一个，终验又反复调，必然能涨。** 修订：候选最多12，S固定，V只准一次去留，不再换针；T只一针两模型，预定97.5%区间，全部失败保留。任何T泄漏之后的修改属于新研究，不能继续用同一T称未见。
7. **0.8B在HumanEval+接近地板，或V症状根本不存在。** 处理：D先有最低可诊断证据；无证据早停。V缺症状支持只能继续检查一般收益，不能称痛点修复；T地板就是边界，不换更容易的题来救结论。
8. **有统计提升但没有实际优势，或损伤数学。** 处理：实践阈值5pp与不确定区间同时满足；简单协议对照和M哨兵分开报告。M仅64题，无法证明无损，不作非劣效承诺。
9. **预算低估小batch和反复加载。** 修订：列出约53M极端输出、加载/TF/验收/失败、CPU最坏时间；4/10为停止线而非保证完成。A首批真实校准，阶段预算不够先沟通；不删对照、压token或把失败免费重跑。
10. **“通用诊断”被固定乘性族过度代表。** 处理：这是通用流程的一个有界实例，明确只有单层8/32通道与有限窗口；阳性不是普适工具，阴性不是所有权重编辑无效。保留用户广义目标，同时不许第一轮无限扩张。

修订后重查 C01/C02/C05/C08/C10/C12/C13/C14：保持原问题，干预、终点、数据和成本一致；没有以“只是探索”免除实际比较。

##### 结论与当前缺口

**设计通过（同助手逻辑自查）。** 数据文件/去重/测试与源码哈希、执行隔离、编程adapter、增益与hook的数值对照、阶段预算账本、服务器编辑器断线运行均待工程验收。来源版本不足或工程无法满足时停在对应步骤，不伪造已就绪。

本次仅方案与CPU文档算术检查，新增GPU/模型/研究编辑器调用均为0；无运行授权。完整执行预算最多0.8B 4 GPUh、4B 10 GPUh，早停可远少于该上限；数学50-pass仍关闭。

---

### 原件 3：WCP阶段调度工程合同

原路径：`experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/CONTRACT.zh-CN.md) · [单独阅读副本](../library/dee18ff408177f13.md)；SHA-256：`dee18ff408177f1385d5d0af184f775c75b2ef2f627a5369b209893eff2d22a5`。

---

#### WCP阶段调度工程合同

2026-11-03，承接0efe0d34与用户本轮明确授权。范围：阶段调度、研究编辑器分阶段访问、服务器断线续接、全流程工程验收和启动清单。正式搜索及研究题生成保持关闭。

实现顺序：持久状态/预算事务→受限编辑器与observer阶段边界→生成、评分、定位、候选和终验适配→CPU合成全流程及故障恢复→服务器后台断线和真实Astra合成握手。复用既有编译干预数值验收，本轮不新增GPU生成；真实编辑器只处理工程合成材料，不读取研究题。登录须使用用户账户，配额/认证不足暂停，不换模型或付费API。

验收成功条件：D→定位→S两轮→冻结→V→T/M→汇总的合成正分支完整；诊断不足、V阴性、预算耗尽正确停止；V只开封一次，不能回改针；编辑器看不到V/T/M及另一模型资料；请求重复/进程崩溃不能重复计分或免费重跑；客户端断开后服务器进程继续，已完成结果重启复用，未确认动作保守暂停。模型工具保持固定原版/编译列增益，不提供任意权重编辑。

工程自查（同一助手，非独立评审）：

|项|结论与理由|
|---|---|
|C01/C02|通过：完善原诊断修复流程的可执行性；合成通过不成为科研增益。|
|C03/C04|通过：复用既有模块/收据；现有Mac控制器断线不能保证服务器续跑，且服务器认证未就绪。|
|C05/C06/C07|通过：不改变BF16编译列增益及下游自然响应；选择阶段和只读确认阶段分离。|
|C08/C09/C10|通过：合成测试只证状态、权限、计账及统计实现，不证定位有效或编程提升。|
|C11|通过：工程失败、科学早停、资源暂停分开；故障残留动作不自动重放。|
|C12|通过：零新增GPU，先复用既有数值证据；CPU假模型接口明确标识。|
|C13|通过：固定配置/来源哈希，持久事务，完整失败日志；独立模型工作目录/会话。|
|C14|通过：交付就绪或具体未通过门槛；正式启动仍需用户指令。|

相关历史E03/E19/E22/E23/E25：少通道不等于小扰动；旧BF16不等价反例保留；样本按题聚类；自查非独立评审；不为调度重做GPU数值或扩预算。其余机制路径类历史错误不适用本次工程补齐，原方案约束继续生效。

最强反方：假模型可以让错误的科研后端看似全流程通过。处理：将真实已验收模型适配、真实隔离评分、真实Astra握手、假模型阶段演练分别列证据；没有长序列实测就不承诺完成ETA。真实登录/编辑器请求失败时不以fixture替代通过。服务端常驻不保证断电/机器重启中的动作自动安全重试，未确认动作需核对后才能续接。

##### 用户选择后的连接修订

服务器登录缓存识别成功，但真实请求路由发现及chatgpt.com直连超时。用户明确选择临时Mac Astra + SSH。仅增加本地回环HTTP桥接，复用相同受限CLI、payload和原始事件；不改科学方案或预算。C03/C13/C14相应补充：服务器控制器可脱离交互SSH，完整流程仍依赖Mac桥接；断线后保存结果并暂停，不能把合成后台验收称为Mac关机后真实编辑器仍可工作。直接连接失败作为独立收据保留，桥接验收另建目录，不覆写失败。

---

### 原件 4：WCP-01 编程工程验收与资源复核

原路径：`experiments/wsp-coding-painpoint-v1-2026-11-03/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/REPORT.zh-CN.md) · [单独阅读副本](../library/bb56a2a1a8e0b7f5.md)；SHA-256：`bb56a2a1a8e0b7f596e29e01778d17f5e64813b2973ae64e2044a088276fbcbc`。

---

#### WCP-01 编程工程验收与资源复核

2026-11-03。本轮完成用户指定的数据、评分器、隔离执行和干预接口工程验收。**未生成 D/S/V/T/M 的模型回答，未调用研究编辑器，未启动数学或编程正式搜索。** 两模型各仅生成 32 条≤128-token 合成样本。工程通过不代表编程能力已经提高，也不代表正式阶段调度器已经完成。

##### 已完成和实测证据

|模块|结果|证据|
|---|---|---|
|固定数据|MBPP 974 条中只取 train 601–974；参考 QA 373/374 通过，927 失败。HumanEval+ full v0.1.10 全部164题参考通过；GSM8K test 1319条。|[来源哈希](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/sources-manifest.json)、[538条参考QA原件（gzip无损）](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/server/receipts/reference-qa.jsonl.gz)|
|源题审查与冻结|88个相似候选保守隔离，另排除31个规范/参考问题；剩254题中固定选 D128、V64、S32⊂D。T164不删题，M64固定抽样。|[排除理由与审查范围](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/data-review.json)、[冻结清单与文件哈希](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/server/receipts/data-freeze.json)|
|评分与执行隔离|14项CPU验收通过：正确/错误、语法/运行/超时/内存、抽取、EvalPlus、权限隔离、按题pass@1、拒绝不完整/故障/重复样本；相同请求复用已记录结果。|[CPU收据](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/server/receipts/cpu-acceptance.json)、[运行输出](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/server/receipts/cpu-acceptance-r2.log)|
|0.8B 编译干预|零增益生成完全一致；±0.5目标列保存/重载逐元素符合公式，其余320张量中的非目标张量不变；流式激活均值与显式读取一致。|[0.8B收据](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/server/acceptance-0p8b-r2/receipt.json)|
|4B 编译干预|同样通过；检查全部426张量的身份和唯一目标矩阵。|[4B收据](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/server/acceptance-4b-r1/receipt.json)|

隔离使用已有 bubblewrap，而非只靠 EvalPlus 的 Python guard：独立 namespace、UID/GID65534、capabilities清零、只读运行环境、无网络/GPU/模型/凭据/宿主数据挂载、临时工作目录。cgroup 限4GB/1核/16进程，另有rlimit与60秒supervisor；并发最多4 worker。生成程序不在权重分析kernel执行。该边界验收不是对Linux内核漏洞的安全证明。

数据审查为本助手的源题/接口/公开测试一致性审查，不是独立审查或参考程序完整正确性的证明。相似度误报也保守隔离，例如面积与周长短程序；这可能改变题型分布，不能称消除了所有语义重复或预训练污染。D/V原测试较弱，后续故障标签仍须检查具体输入与规范。公开示例包括原MBPP测试；其开发分数不当作隐藏泛化成绩。T仅在未来终验使用。

##### BF16差异按用户选择处理

0.8B最初验收确实失败：[原始收据](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/server/acceptance-0p8b-r1/receipt.json)。λ=+0.5时，运行时激活增益与编译权重增益的最大 token log-prob 差为 **0.0755806**，超过旧0.05门槛；4B对应差为 **0.1193173**。原阈值没有提高，失败记录没有删掉。

用户明确选择保留编译权重干预。本轮主操作因此为 `W'[:,J]=BF16(float32(W[:,J])*(1+λ))`；运行时针只是诊断，不能把它的读数当成编译针的同义证据。已同步修订[方案](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-coding-painpoint-v1-2026-11-03/PLAN.zh-CN.md)和[自查](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-coding-painpoint-v1-2026-11-03/SELF_CHECK.zh-CN.md)。固定L0前8坐标只是工程fixture，没有从研究题选针。

另保留了脚本调用、cgroup异步清理和慢去重实现的失败/中止日志；修复后重新验收。仅移除了已结束任务的空cgroup以及本工程可重建完整checkpoint副本。原始数据、生成、快照、矩阵差分、构建记录和日志保留。大矩阵在服务器，逐文件哈希见[最终审计](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/server/receipts/final-audit.json)；Git中交付文本证据与来源清单，不提交模型或环境。

##### ETA与磁盘重新核算

|实测项|0.8B|4B|
|---|---:|---:|
|成功合成验收设备墙钟（含加载/构建）|193.88秒|226.91秒|
|失败验收设备墙钟|7.54秒|0秒|
|累计工程计账|201.42秒，约3.36分钟|226.91秒，约3.78分钟|
|四臂纯生成合计|13.26秒，3465 tokens|16.19秒，4096 tokens|
|阶段A原停止线中剩余|1598.58秒|3373.09秒|
|全流程原停止线|4 GPUh|10 GPUh|
|新增磁盘规划额度|25GB|40GB|

两模型共计 **428.33设备秒、64条合成生成、724个TF输入tokens**，已计入原预算，没有另开验收赠送额度。538份参考QA的逐程序墙钟总和约75.06秒；并行总耗时不同，不能称75秒CPU核时，也不能据此保证模型生成的错误程序一样快。

**目前无法确认完整研究的完成ETA。** 本次128-token、batch-8 eager合成生成约261/253 token/s，与原FA-01的4096-token批量吞吐处于不同工况，不能混用。此前按14,045/5,124 token/s算出的约1.05/2.87小时仅为历史吞吐假设下的极端输出解码算术，不是本任务预测。4/10 GPUh保留为停止线，不承诺在其内跑完所有阶段。若把本次小批量短生成速度机械外推到52.96M极端输出，会得到约56/58小时，仅说明估计对工况敏感，同样不是预测。

长输出16k吞吐、实际提前停止比例、TF的参考PyTorch慢路径、Astra周转与配额仍未实测。正式授权后只利用已经预算内的首个D固定批次校准ETA；若超阶段预算，暂停商量，不另跑吞吐实验或减少对照。CPU每程序60秒、最多4worker的极端墙钟可超过11小时/模型，故GPU小时不是端到端交付时间。现金金额需实际卡费/账号计费，不能从额度推定。

2026-11-03 21:35（UTC+8）实测：服务器 `/workspace` 可用 **269.57GB**；WCP目录文件合计 **0.458GB**，包含保留的编辑矩阵/快照；两张H20均3MiB、利用率0。已有0.8B/4B权重约1.505/8.412GB，直接复用。当前无需新增模型下载，也无需数百GB额外空间。

21:40[收尾检查](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/server/receipts/closeout-state.json)：空闲空间仍269.57GB，本轮使用的GPU0已释放；GPU1随后出现9857MiB占用，本轮未在GPU1运行验收，也未干预该任务。所有WCP临时cgroup已清空，数学两份正式配置仍 `authorized=false`。

编程两模型25+40GB工作额度与共享50GB余量合计115GB，现有空间足够。若数学线50+100GB也全部增长到上限，两线合计215GB新数据+50GB保留线=265GB，仅比当前可用少约4.57GB；不能同时把全部余量重复承诺。顺序执行并逐阶段核实际增长；在原地归档不会释放磁盘，不删除旧证据来满足预算。

##### 接下来与启动边界

本轮四类工程已通过。正式运行前仍需把这些适配器接入 **WCP的阶段状态机**，冻结候选/只开封一次V/终验权限、候选与token总账、随机对照校准、分析汇总，并验收服务器编辑器断线续接。已有数学50-pass调度不能直接替代这套流程；现有源码只提供工程worker与评分适配器，没有自动启动正式搜索的入口。

D可挂载目录与observer-private已分离；评分沙箱无法读取宿主数据。未来研究编辑器的D-only挂载与阶段开封需随WCP状态机验收，不能把目录权限本身当作整条编辑器信息隔离已经证明。当前所有正式授权开关仍为false。本轮不启动搜索，也不把工程通过称为完整研究已可无人值守运行。

---

### 原件 5：WCP-01 编程工程验收

原路径：`experiments/wsp-coding-painpoint-v1-2026-11-03/README.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/README.md) · [单独阅读副本](../library/187bc374d0f88058.md)；SHA-256：`187bc374d0f880585304bda5ca6b9a0d07f1ad1bf7fc047fdd69b081488b9b65`。

---

#### WCP-01 编程工程验收

**本轮阶段调度已收尾：** [启动清单与剩余预算](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/STARTUP.zh-CN.md)。调度/分阶段编辑权限/恢复验收通过，真实Astra采用用户选择的Mac→SSH路径；Mac需在线。正式搜索保持关闭；旧版报告中的待补齐范围由本轮收据更新。

**四类验收与资源复核已完成：** [REPORT.zh-CN.md](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/REPORT.zh-CN.md)。数据、CPU评分/隔离、0.8B和4B编译干预通过；正式搜索未启动，完整研究ETA尚不能确认。WCP阶段调度与编辑器信息开封的剩余范围见报告末节。

**工程修订r2：** 首次0.8B BF16 runtime/compiled等价检查未过，已停止并获得用户明确选择：主操作保留编译权重增益，不称运行时针的等价实现。新的主验收为目标列按float32增益再BF16舍入逐元素相同，其余全部张量不变、零增益生成一致；runtime比较只保留诊断，不提高旧阈值。完整修订自查见方案SELF_CHECK顶部。下方初版等价要求按此修订理解；原失败收据保留并计入预算。

2026-11-03。依据[方案](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-coding-painpoint-v1-2026-11-03/PLAN.zh-CN.md)及本轮用户明确授权：补齐数据、评分、隔离与干预接口，完成工程验收，复核 ETA/磁盘；**不启动数学或编程正式搜索**。

##### 本轮验收合同

- CPU：固定版本 MBPP / HumanEval+ / GSM8K 数据来源与哈希、参考解答和分区；代码抽取、正确/错误/语法/运行/超时判定；bubblewrap独立namespace、UID/GID65534、capabilities清空、无模型/凭据/网络/GPU，cgroup与rlimit约束。
- GPU：每模型仅4条合成提示×2种子×原版/零针/−0.5/+0.5四臂，最多32个≤128-token回答；短固定文本TF检查λ=−1/−0.5/+0.5/+1的runtime与编译干预、零针、FP32恒等式、流式统计。针眼固定L0前8坐标，仅用于工程，不作为科研候选。
- 0.8B工程设备时间≤1800秒、4B≤3600秒，纳入原方案A阶段。外层timeout包含加载与失败；等待他人GPU不抢卡，不在等待时加载模型。CPU评分使用最多4worker、单程序≤60秒/4GB/1核/16进程；全组运行有单独外层限时。
- 本轮不生成D/S/V/T/M的模型回答、不调用研究编辑器、不选择科学针。参考代码执行属于CPU评分验收，不是模型实验。
- 验收差异与失败原件保留，新修订用新收据；原始权重、旧实验、日志、快照、构建记录不删除。仅清本工程私有可重建完整checkpoint副本，保留来源快照与build记录。

##### 设计自查增补（同一助手，非独立审查）

设计卡：问题为新任务的工具是否按已批准协议执行；增量为评分、隔离、数值与资源实测可信度；复用旧WSP加载/快照/Reader/vLLM；操作仅CPU参考和固定短合成GPU输入；终点为身份、得分、权限边界、数值容差、时间与空间；失败不改标准制造通过；授权来自本轮用户工程验收指令，正式搜索仍禁止。

|条目|判定与理由|
|---|---|
|C01/C02|通过：支撑编程能力修复研究，不把工程分数称科研增益。|
|C03/C04|通过：固定来源和既有工程复用；原始MBPP参考可能错误、BF16等价可能失败，必须实际验收。|
|C05/C06|通过：具体hook/编译操作同原方案，L0前8是合成fixture，不用于推断科学选点；下游自然响应。|
|C07/C08|通过：恒等式有精确算术条件，BF16实际误差独立测；无缓存路径或唯一根因主张。|
|C09/C10|通过：错误评分/非法权限/不一致快照/数值偏差有直接拒绝判据，不以模型回答正确代替。|
|C11/C12|通过：失败为工程阻塞；限短合成输入与CPU参考，复用旧吞吐，不启动长序列基线伪装验收。|
|C13/C14|通过：来源哈希、代码身份、日志与退出状态分开记录；通过后只交付就绪情况，不能自动开始搜索。|

重点复查E03（少通道不等于弱扰动）、E19（代数/工程不是科学发现）、E22/E23（合成验收不是独立能力复现）、E25（不为ETA重跑完整基准）。其他原方案E01–E26处理继续有效。

反方：短输入通过仍不保证16k运行性能或长期可靠性。处理：报告实测加载/短生成/CPU评分，长输出ETA明确保留条件与停止线；绝不承诺“短验收证明正式全部可完成”。数据通过原测试也不能证明规范完美，因此参考QA与语义/重复审查分别记录。

##### 实现

- prepare_sources.py：固定来源，小文件下载，清单与SHA256。
- isolated.py / scoring.py：只读挂载、干净环境、namespace+cgroup隔离，冻结抽取和原版EvalPlus规则。
- prepare_data.py：CPU参考核验、疑似重复审计、确定性开发分区草稿；审查后才冻结。
- freeze_data.py / data-review.json：记录源题审查、冻结D/S/V/T/M及提示哈希；observer私有资料与D挂载目录分开。
- score_batch.py：observer评分日志、重复请求复用、按题pass@1；不完整或执行器故障拒绝报告完整分数。
- model_interface.py：复用WSP前向，编程提示/采样、全位置增益、编译快照、流式激活统计。
- cpu_acceptance.py / gpu_acceptance.py：固定fixture验收，没有正式搜索入口。

实际结果以本目录后续 REPORT 和 receipts 为准。本合同不预填通过。

---

### 原件 6：WCP 最小正式启动清单

原路径：`experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/STARTUP.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/STARTUP.zh-CN.md) · [单独阅读副本](../library/a7437672bf8c991c.md)；SHA-256：`a7437672bf8c991c46e39804c59bb62d362fdc05400e87796974035648e1d87a`。

---

#### WCP 最小正式启动清单

本次只补齐阶段调度、编辑器权限和服务器续接，正式搜索仍关闭。原始数据、已验收模型、编译干预与科学判据继续沿用上一轮。最终通过状态和实测用量以本目录receipts中的收据为准。直接服务器Astra请求失败日志完整保留；验收必须明确标记为Mac桥接路径。

##### 本轮收尾结果

- 合成全流程与故障恢复11项通过；服务器隔离评分、BF16校准和两模型真实tokenizer适配通过。
- 真实Astra经Mac/SSH两个独立会话通过，共77.06秒；0.8B记6,304输入/472输出，4B记6,304输入/717输出，各1回合。均未使用原生工具。
- 原直接服务器连接因路由超时失败，旧失败事件保留；不是账户登录失败，也不是GPU加载缓慢。
- 服务器后台合成流程在原SSH结束后完成；实际桥接仍依赖Mac，不能把该检查解释成现在可以关闭Mac。
- 本轮零新增GPU生成，未生成研究题回答，未开启50-pass或WCP正式搜索。

##### 已实现的执行路径

`D原版 → 全失败标注/诊断门槛 → 配对激活定位 → S的8+4候选 → 随机对照校准/冻结 → V六臂一次开封 → 通过才做T四臂与M哨兵 → 按题配对报告`。

诊断不足、随机校准无效、V阴性直接结束分支；工程失败、配额、数据身份变化和预算问题暂停。GPU只取空闲卡，等待不占GPU预算。现有数值验收直接复用，没有再跑模型。

编辑器使用Mac上的 `gpt-6-astra/max`，经仅监听127.0.0.1的SSH隧道连接服务器。用户在服务器直连超时后明确选择此临时路径。它接收观察者构造的结构化输入，不开放原生工具或通用Python执行：诊断角色只见D，验证角色在针和规则冻结后只见V；T/M只由观察者生成和评分。两个模型目录与会话隔离。分类按批使用新会话和显式规则，避免依赖Mac上的历史会话；候选排序和去留由固定代码执行。标签是带证据的语义解释，不是已证实的唯一故障机制。

阶段、请求身份、结果与预算保存于服务器SQLite。重复请求复用已提交结果；已产生完整结果但尚未提交时可显式核对恢复。无法确认的动作不自动重跑，保留原日志并报告。服务器tmux保持控制器和模型任务独立于交互SSH；**本轮实际采用Mac编辑器，Mac关机、休眠或桥接SSH断开后，后续编辑器调用会失败暂停，不能承诺整条流程继续。** 已完成结果保留，未确认动作不自动重放。服务器断电/重启也不保证在执行动作自动恢复。

##### 正式启动前，只检查这些

1. 获得用户对0.8B正式运行的明确指令，再填写 `search-0p8b.json` 的 `authorized=true` 与 `authorization_record`。目前仍为false；4B保持独立关闭，不随0.8B自动启动。
2. 核对全流程验收收据、固定数据与源码哈希。模板已经绑定这些身份，发生变化会拒绝启动。
3. 查看磁盘空闲，保留50GB；只等空闲GPU，不终止其他任务。确认Mac登录、桥接进程和SSH隧道有效；Mac保持接电、开盖和联网。
4. 启动后只利用已预算的首个D批次校准长输出ETA；不再预跑一轮“更全面”的准备实验。超预算暂停，不缩短答案上限或删对照。

Mac桥接启动命令（只启动编辑器服务，不启动搜索）：

```sh
caffeinate -i python3 /Users/ruizhixu/Documents/ChatGPT/acupuncture/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/mac_editor_bridge.py \
  --out /Users/ruizhixu/Documents/ChatGPT/acupuncture/external/wcp01/mac-bridge-r1/calls
```

已有桥接进程时不要重复运行。桥接日志和原始调用保留在该本地目录；成功返回的调用证据也同步到服务器。`caffeinate -i`只阻止空闲睡眠，不保证合盖后工作。

服务器目录：`/workspace/acupuncture/external/wcp01/code/orchestration`。

授权前可检查配置，预期返回 `FORMAL_SEARCH_DISABLED`，不会创建正式run：

```sh
sh /workspace/acupuncture/external/wsp/code-engineering-r2/engineering-r2/server_env.sh \
  /workspace/acupuncture/external/wcp01/code/orchestration/scheduler.py \
  --check --config /workspace/acupuncture/external/wcp01/code/orchestration/search-0p8b.json
```

仅在授权记录填写后，运行一次服务器启动命令即可退出SSH：

```sh
sh /workspace/acupuncture/external/wsp/code-engineering-r2/engineering-r2/server_env.sh \
  /workspace/acupuncture/external/wcp01/code/orchestration/launch.py \
  --config /workspace/acupuncture/external/wcp01/code/orchestration/search-0p8b.json
```

同一命令加 `--status` 查看阶段与账单。若控制器停止，核对日志后用相同配置重启；不要改run目录逃避已用预算。仅有已完整保存的结果才可用 `--recover-completed 动作ID` 核对后恢复。其余未确认动作联系观察者处理，不自动重跑。

##### 剩余预算与性能边界

收尾时服务器可用266.19GB；两模型合计规划65GB，加50GB保留量共115GB，空间足够。WCP目录约1.37GB（包括新CLI与下载缓存）；该数字不包括复用的WSP模型。GPU当时两张均空闲，此状态随其他任务改变。未创建正式run目录。详细证据：[汇总](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/receipts/acceptance.json)、[资源](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/receipts/resources.json)、[禁用检查](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/receipts/disabled-gates.json)、[完整原始归档与哈希](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/receipts/archives.json)。


|项目|0.8B|4B|
|---|---:|---:|
|总GPU停止线剩余|14,198.58秒（3.944小时）|35,773.09秒（9.937小时）|
|阶段A剩余|26分38.58秒|56分13.09秒|
|阶段B / C|1.5 / 2小时|4 / 5小时|
|研究回答最多|2,976条|2,976条|
|TF输入token剩余|1,999,542|1,999,734|
|CPU可用预算|58 core-hours|58 core-hours|
|工作磁盘规划|25GB|40GB|
|编辑器回合剩余|99|99|
|编辑器输入token剩余|1,493,696|1,493,696|
|编辑器输出token剩余|149,528|149,283|

GPU已经扣除上一轮所有成功/失败验收，本轮没有新增GPU开销。CPU为历史准备阶段未精确计核保守预留2 core-hours/模型，**是预算分配，不是声称实测用了2小时**。新的执行按实际CPU用量记账。真实Astra握手消耗从各模型100回合、1.5M输入/150k输出额度扣除，精确余额见 `receipts/remaining-*.json`。直接服务器请求未产生turn.completed用量，不能据此声称提供方确定未计费；原始错误事件保留，不伪造token用量。

CLI能读取每次调用实际用量，缺失会停止；token额度是调用前检查与调用后停止线，**不是提供方单次生成硬截断**，最后一轮仍可能超线；发生时记录实际消耗并暂停，不能称已实现不可超额硬限。新会话按每次实际用量记账，不重复累加会话累计数。

4/10 GPUh仍是投入停止线，不承诺全部跑完；16k实际吞吐和错误程序耗时尚未知。工程演练的模拟分数不可用来声称能力提升，假模型GPU账单也不计作真实GPU耗时。Astra语义标签仍需结合失败输入、规范和代码核对，精确引用检查本身不证明语义归因正确。

本次准备遵循用户“不要过度工程”的纠正：不再扩充平台、追加GPU验收或重做旧模块。服务器认证沿用用户授权的本机登录缓存，经SSH写入0700私有目录/0600文件，凭据不进入Git或日志；方法依据[官方无浏览器登录说明](https://learn.chatgpt.com/docs/auth#login-on-headless-devices)。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [orchestration/receipts/adapters-r1--receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/receipts/adapters-r1--receipt.json) | {"status": "passed"} | {} |
| [orchestration/receipts/disabled-gates.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/receipts/disabled-gates.json) | {} | {} |
| [orchestration/receipts/disconnect-r1--launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/receipts/disconnect-r1--launch.json) | {"mode": "fixture"} | {} |
| [orchestration/receipts/disconnect-r1--receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/receipts/disconnect-r1--receipt.json) | {"status": "completed", "mode": "fixture"} | {} |
| [orchestration/receipts/flow-r1--receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/receipts/flow-r1--receipt.json) | {"status": "passed", "scope": "synthetic_control_flow_not_model_or_capability_evidence"} | {} |
| [orchestration/receipts/live-mac-r1--receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/receipts/live-mac-r1--receipt.json) | {"status": "passed"} | {} |
| [orchestration/receipts/live-r1--receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration/receipts/live-r1--receipt.json) | {"status": "failed"} | {} |
| [receipts/server/acceptance-0p8b-r1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/server/acceptance-0p8b-r1/receipt.json) | {"scope": "synthetic_engineering_only", "status": "failed"} | {} |
| [receipts/server/acceptance-0p8b-r2/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/server/acceptance-0p8b-r2/receipt.json) | {"scope": "synthetic_engineering_only", "status": "passed"} | {} |
| [receipts/server/acceptance-4b-r1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/server/acceptance-4b-r1/receipt.json) | {"scope": "synthetic_engineering_only", "status": "passed"} | {} |
| [receipts/server/receipts/final-audit.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/server/receipts/final-audit.json) | {} | {"time_utc": "2026-11-03T13:35:07.695039+00:00"} |
| [receipts/server/receipts/storage-audit.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/server/receipts/storage-audit.json) | {} | {} |
| [receipts/storage-audit.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/storage-audit.json) | {} | {} |

## 全部原始资产入口

本目录在固定提交下共有114个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/115-wsp-coding-painpoint-v1-2026-11-03.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-coding-painpoint-v1-2026-11-03)。未复制模型权重、环境或凭据。
