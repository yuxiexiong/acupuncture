# 137．WSP VLM v7开放修补首轮

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-05；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

B/C研究者在原开发集自主查看失败、测量和提交稀疏补丁；固定保护指标、预算和评价。

**实际过程、结果与后来更正**

发生权限和连接等工程问题，旧评价有远端继续运行而本地断线的情形。原请求、反馈和失败保留，不能把通信失败当科学阴性；接续版本见v7r1/v7r2。

**来源身份**：`wsp-vlm-open-repair-v7-2026-11-05`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：v7执行合同：B/C开放修补首轮

原路径：`experiments/wsp-vlm-open-repair-v7-2026-11-05/PLAN.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7-2026-11-05/PLAN.zh-CN.md) · [单独阅读副本](../library/22cd3431377635b7.md)；SHA-256：`22cd3431377635b7ea46b6afb86b86b1c027e15d751c6441164f4cf02f5413cb`。

---

#### v7执行合同：B/C开放修补首轮

2026-11-05；用户在推进方案后明确回复“同意，推进吧”。授权范围承接[推进方案](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-vlm-bc-continuation-v1-2026-11-05.zh-CN.md)：共享工程1单卡小时、B与C各2单卡小时。授权不扩展到新模型、新任务、LoRA或独立终验。先真实工程验收，后两个分开的AI探索；任何失败保留。

##### 固定项与数据

目标Qwen3-VL-4B-Instruct固定revision、BF16/SDPA/greedy128及处理器与S0相同。B仅D58组/464请求，C仅D64组/2560请求供搜索，带全部原版raw、标签、问法/顺序和两种提示；资料hash见audit/development_export.json。H不提供给搜索会话；已有H分析已影响本设计，不能再称新独立确认。候选冻结后旧H回归若本轮额度不足则留待后续，不能越过2小时追加。

WSP循环：AI读完整反馈→自己提出可检验想法→选测量或直接权重试改→自己选参数、支持集合和非梯度计算→服务同输入比较原版/父候选/候选→AI根据修对/改错继续、回退或停止。参数目录不限制层、视觉/语言组件、MLP/注意力。最终是同架构静态权重补丁，正常推理不含研究者或诊断hook。

##### 数值合同（prepare_live.py生成并hash冻结）

- 工程：累计至多3600秒单卡占用，所有失败加载/重放计入；工程CPU/研究者测试另记墙钟。人工指定的三个组件各一标量只测试存储、回滚与重载，不作为科学候选，也不传作研究者选点建议。
- 每分支：墙钟7200秒，含加载、AI等待、CPU诊断和评价，因此单卡占用不超过已批准2小时；100研究者回合/100操作上限，CPU工具累计1200秒。
- B至多12000前向样本、5000万保守目标token预留；C至多24000样本、1亿预留；每请求输入4096token、生成128token。失败不退额度，先到任一上限即停止。更多C样本额度用于其完整开发包较大，并非追加墙钟。
- 单次内部导出至多200万标量。临时候选相对W0最多400万变化标量，最终最多100万；对约4B模型分别约0.1%和0.025%，这是有限试验资源边界，不是推导出的可修阈值。跨层、头、行列和低秩实际变化都按唯一标量计数；不得以绑定别名绕过计数。没有效果不自动扩上限。
- 研究者沿用旧数学配置gpt-6-astra/max、已有ChatGPT登录；不购买额度、不切换API计费。每分支累计input+output token观察限500万，达到后不再发下一轮，允许最后一轮usage超出该观察限；100轮/7200秒是硬限。登录身份强制chatgpt并删除子进程API-key环境。订阅可能占用账户额度，实际美元成本未知，不能把token或虚拟预留额当账单。这取代v6不适用于当前订阅路径的必填美元字段；计费API路径仍需金额和外部费用限制。

##### 选择规则

B目标：普通提示每组每问法“全数与子集两题全对”，先组内平均再组间平均。C目标：普通提示每组每问法/顺序“反事实通常与反事实视觉两题全对”，同样组内平均、组间等权。五条件全对和每格正确率均另报。初始D目标B=0.4741379310，C=0.5859375，来自已有raw复算，不是修补结果。

任何晋升必须先完成全部固定D输入，局部试改只供诊断。对B两条件、C五条件的每个提示×问法×顺序格，相对W0正确率下降不得超过0.035（B58组、C64组均最多净损失2组/格）；格式失败率、截断率各不得超过1%。这些是初轮可接受开发损伤上限，不是统计非劣效证明；每格修对/改错完整报告。目标分数优先，平分优先更少变化标量；W0仍可保持最佳。保护包含规则提示，避免普通提示涨分却使规则提示明显崩坏。部分候选有科学线索但未过保护，可以保留分析而不能晋升最终补丁。

研究者不能读H、改标签/评分/模型设置、绕服务跑前向或训练权重。可自写NumPy算法；当前内部测量支持通用模块输入/kwargs/输出、坐标干预和teacher-forced分数，不含任意求导或专用注意力概率提取。工具缺项单独报告。候选数和有效修改次数不预定，不强迫交付成功补丁。

##### 验收与自查

复用总方案及推进方案的设计卡/C01–C14；本次数值落实后的复查：C01/C02保留AI可修性主线与实质增量；C03复用raw和v6代码，另建v7保留旧证据；C04阴性和损伤均允许；C05/C06每次记录静态差分及正常下游响应；C07绑定别名核查；C08只评有限开发修复，不称机制或AI搜索优越；C09诊断预测由AI逐轮给出；C10多问法组级自然答案终点；C11工程与研究分离；C12数值预算如上，失败计账；C13已见H边界清楚；C14预算结束不自动加码。十四项设计层面通过，真实工程验收另记，不冒充已经通过。

历史错误重点复查：E02不预选层；E03同时报告支持数和范数；E10不拿logit当正确答案；E11不因探针阴性排除；E12不以差距收窄掩盖控制损伤；E16保留有效阴性；E20允许多原因；E21未开展新颖性确认；E22来源组计样本；E23同一助手自查；E24不等完整机制才试改；E25不展开额外消融。其他历史缓存拆换错误本轮不涉及其操作。

反方检查：旧选择器会漏T1损伤，已加入多问法目标及逐格保护并用“均分不变但T1变坏”反例测试；开发过拟合仍可能发生，故不作泛化结论；100万支持上限可能找不到有效补丁，阴性仅限此预算；订阅usage不是美元成本，明确未知且无API回退；工程挑三个组件不能冒充AI诊断，隔离保存、不传给研究者作为答案。自主搜索费用与方法全部留痕，合成测试不替代真实会话。

---

### 原件 2：原始文档

原路径：`experiments/wsp-vlm-open-repair-v7-2026-11-05/RESEARCHER.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7-2026-11-05/RESEARCHER.md) · [单独阅读副本](../library/c1ce04c7e05a3933.md)；SHA-256：`c1ce04c7e05a39338489e06cd775b544bad1cebc7e9dc60f24f5ec94dfbcafd5`。

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

This is the first bounded development exploration after original-model screening.
Use all available development successes and failures, not only a preselected error
pattern. Read /evidence/bundle.json using Python for the complete package; it
includes previous_predictions. The human has not established a failure mechanism.
B concerns total vs spatially conditioned counts. C concerns visual vs usual
size judgments under original/counterfactual images and no-image controls.
Do not assume a missing neuron, a particular layer, or one shared cause.

Selection: ordinary-prompt joint correctness, averaging wording/order within each
source group then groups equally. B pairs total/subset; C pairs counterfactual
usual/visual. All conditions and both prompt arms are protected per wording/order
cell: maximum 0.035 accuracy loss vs original, format/truncation each <= 0.01.
Only full fixed development evaluation can select a best candidate. Ties prefer
fewer changed scalars. C's original/no-image controls and five-way correctness
must also be reported. View raw responses and repaired/worsened IDs.
Temporary support <=4,000,000 and final support <=1,000,000 actual BF16 scalars
relative to W0, across any legitimate parameter locations. Wall limit 7200 seconds
includes your thinking time, model loading, diagnostics and evaluations. No need
to use all 100 turns. Budget exhausted or no useful patch is a valid outcome.
Your persistent CPU workspace has NumPy only; use the metered observer for every
model forward. Select your own observations and edit computation. You may change
your hypothesis using feedback; an engineering error is not a task failure.

---

### 原件 3：B/C筛查之后：两条线共同进入开放修补探索

原路径：`docs/wsp-vlm-bc-continuation-v1-2026-11-05.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-vlm-bc-continuation-v1-2026-11-05.zh-CN.md) · [单独阅读副本](../library/511b03563087408f.md)；SHA-256：`511b03563087408fef886116664e0ddb7341e0d05090038997f21fc2dc091de4`。

---

#### B/C筛查之后：两条线共同进入开放修补探索

日期：2026-11-05。身份：筛查后推进方案和同一助手自查；本次没有模型调用、内部测量或权重修改。用户决定B、C均继续推进。本文件更新[总方案v2](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-vlm-ai-repair-plan-v2-2026-11-05.zh-CN.md)中“至多选择一个优先对象”的安排，不改写已完成筛查的判定、数据或统计。本文件是阶段计划，尚不是可启动的数值执行合同。

##### 1. 为什么两条线都继续

依据是[已完成筛查及原始证据](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-failure-discovery-run-v1-2026-11-05/REPORT.zh-CN.md)，提交`d149389d39dec2e108d57825d25179ecd1e79b21`。

| 分支 | 已观察到什么 | 下一步值得问什么 |
|---|---|---|
| B：空间条件计数 | H的88组中，全数73组对、空间子集60组对，差14.77pp；校正p=0.02945；换问法仍差15.91pp。22组全数对而子集错，9组反向 | AI能否找到有用的修改，使模型更可靠地按空间条件计数，同时保留全数能力？ |
| C：视觉与通常常识的适用范围 | H的96组中，原图通常94组对、反事实图通常74组对；15组符合严格跟图错误模式。反事实视觉问法T0有90组对，T1只有59组对 | AI能否改善按问题选择依据的行为，同时让视觉题、常识题和不同问法都受益？ |

B的原15pp是资源分配门槛，与14.77pp相差0.23pp没有自然能力边界。保留历史“未达到预定门槛”，现在根据完整证据与用户决定进入探索，二者不矛盾。不是把阈值改到刚好通过，也不是补题凑通过。

B不能预设为“忽略条件”：在全数与子集标签不同的59组中，只有2组出现全数答对、子集错答成全数。C也不能预设为“视觉权重过高”：另一种视觉问法本身就明显失败，统一削弱图像可能适得其反。固定规则提示没有稳定修好这些问题，但这只说明该提示的局限，不证明WSP会成功。

##### 2. 中心猜想和本轮增量

**在这两个任务中，可能存在跨实例共享、可通过少量现有权重修改改善的计算行为；研究者AI可以依据测量和试改反馈逐步发现这样的补丁。** 少量权重可修、AI能找到、能在新材料上泛化，是三个待验证命题。

本轮从已完成的S0进入S1/S2：先让真实工具闭环可靠，再分别做有限的开发探索。首先争取获得“可重载、可复核、有净修复且损伤明确”的候选或有信息量的失败记录；不要求先证明完整机制。两条线分别起会话、从同一原版W0开始、分别保存补丁，不假定病因相同，也不一开始合并修改。

##### 3. 实际推进顺序

###### 第一步：把现成证据交到AI手里，先做离线工作

1. 将本次真实D回答、标签、原图与处理器预览、普通/规则提示、两种问法和全部成功/失败接入v6证据包。B沿用58组、464输入，C沿用64组、2,560输入；核对每个ID、来源hash、原版预测及评分，不只挑典型失败。
2. 给AI开放完整D材料和工具说明。人类观察到的模式标为线索，允许AI否定、重新分类和提出其他解释。B可探索识别、参照物、关系判断、集合筛选或计数等环节；C可探索问题范围、图像与知识使用、措辞等环节。这些不是强制诊断顺序或封闭菜单。
3. 已看过的H不再叫修补独立终验。首轮仍用D反复搜索，旧H只在候选冻结后作一次已见回归面板，不向搜索会话逐轮反馈。此隔离减少直接拟合，但研究设计已受H启发，不能宣称H完全未见。

交付：真实反馈包、来源清单、数据可见范围、尚缺工具清单。复用原版回答，不为整理材料重新跑全套筛查。

###### 第二步：真实编辑工具的短工程验收

[v6](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v6-2026-11-05/README.zh-CN.md)已实现通用参数目录、按需权重读取、AI Python操作、任意命名模块测量、静态候选、回滚和配对反馈；已通过合成离线测试。其README中“S0未执行”是当时状态，现已由本次筛查补齐；其他真实编辑验收没有因此自动完成。

先在既有D案例上验证：原版无操作重放一致；真实模块/绑定别名及张量位置正确；一次小型工程差分能够正确应用、撤销、保存、重载；去掉诊断hook后权重和输出身份一致；异常退出不残留补丁；Linux隔离和研究者CLI的文字/图片往返正常。工程差分不按任务得分优化，不充当“发现神经元”。

验收失败先修工具，不把失败算成WSP科学阴性。当前仍缺研究者模型/CLI版本、费用凭据、隔离运行环境实测、真实模型视图和验收回执。专门注意力概率、任意诊断求导等并非现成工具；若AI确有需要，再补必要接口并验收，不用工具缺项否定一个位置。

###### 第三步：B、C各做一轮有预算的开放探索

每轮循环如下，轮数由已冻结总预算与AI判断共同决定：

1. **AI读反馈并提出下一步。** 可以先测内部量，也可以直接试改；记录预期、依据和反例，不要求先完成病因证明。
2. **AI选择实际参数和修改计算。** 不限定两层、MLP、注意力头或神经元排名。可在视觉编码、融合和语言解码等合法参数中选择；允许符合既有非梯度合同的自编计算，不把已有算子当菜单。
3. **服务应用并测试。** 保存相对W0的真实BF16差分、父候选、实际变化标量数、范数和代码。局部自选题只能作诊断；晋升候选须在完整固定D包上评分。
4. **把原始回答和修对/改错返回AI。** 同时比较原版、父候选、新候选；AI可换点、换强度、换方法、改解释、撤销或停止。
5. **冻结候选并重载复核。** 交付同架构静态补丁，普通推理不需要研究者、逐题路由或诊断hook。随后才检查旧H的已见回归表现。

**WSP就在第2—4步：AI依据反馈直接修改训练后模型的少量现有权重，并反复用真实效果修订修改。** 内部读数和激活干预只是可选诊断；最终效果必须来自静态权重。最终稀疏性按实际改变的唯一标量计，不把低秩等同稀疏，也不因涉及多层就拒绝。暂时试改与最终交付的总标量预算须分别冻结。

##### 4. 怎样比较，怎样避免“涨分但没有修好”

模型继续固定Qwen3-VL-4B-Instruct，revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`；处理器、输入、BF16/SDPA、greedy、128新token和评分器不变。每次请求清空会话状态，下游激活正常响应权重变化。因此比较估计的是补丁的整体行为效果，不是某条内部路径的独立贡献。

| 分支 | 主要目标与配套读数 | 必须防止 |
|---|---|---|
| B | 普通提示下全数与空间子集联合正确率；分报子集、全数、两种问法，以及每格修对/改错 | 靠统一减小数字提高子集分，却破坏全数或不同空间关系 |
| C | 普通提示下同图通常题与视觉题联合正确率；分报五条件、五条件全对、两种问法和两种顺序 | 只提高常识题却破坏看图；只修T0却恶化T1；全局偏好某个选项 |

分格先按来源组内平均，再按来源组等权；所有问法/顺序均保留，不能挑最佳面板。开发选择的主指标、保护界限、平分规则要映射到服务并在搜索前冻结。v6目前的“主条件联合正确率”不能直接当作上述多问法目标已经实现，需先离线核对和必要修改。

固定四种比较：原版＋普通提示、原版＋现有规则提示、补丁＋普通提示、补丁＋规则提示。原版结果在身份一致时复用；补丁用完整D包自然覆盖两种提示。现有规则提示不是“最强提示基线”。前期不为每个候选加全套LoRA/其他编辑训练；若候选有希望，再补与实际主张相关的近邻和成本比较。

开发提高仅提供线索，不在反复搜索的D上宣布显著成功。不能只看控制与挑战的差距缩小，因为控制变差也会缩小差距。保留全部修对/改错和保护损伤；有收益但有损伤的候选可作为探索轨迹保存，不冒充合格最终修补。保护阈值尚未冻结前，不启动候选自动晋升。

##### 5. 成本、时间和阶段出口

先安排半个工作日量级的离线反馈包及配置整理，再做真实工程验收，之后让B/C各获得同等第一轮探索额度。这是工作估计，不是已发生耗时或完成承诺。

资源规划建议：共享工程验收预留至多1单卡小时；B、C初轮各预留至多2单卡小时。单卡占用计入加载、诊断、试改、回滚和评价；若等待研究者时持续占卡也计入。已测B_D约60秒、C_D约249秒，只能估算纯评价量级，不能当开放搜索的ETA。C评价较贵，不因此机械给两条线相同评价次数；分别记完整开发包评价数、诊断样本数、前向/token及GPU时间。

这些为待批准的资源建议，**不挪用已结束S0的剩余预算**。运行前还须填完并冻结：研究者身份与美元上限、会话/动作/前向/样本/token上限、墙钟与CPU限额、张量导出限额、临时/最终标量上限、保护界限和真实验收hash。当前模板数值为空，故本文件不宣称可以直接开跑。数值限制约束花费和补丁大小，不能变成指定层/神经元配方。

第一轮结束分别给B/C一张结果卡：AI提出过什么、测过什么、改了哪里、最好与最坏候选、修对/改错、损伤、支持数、成本、是否经重载、哪些解释被撤回。按下列证据决定追加工作，不再用15pp作修补准入门：

- 有可重载的净改善、保护项可接受：冻结候选，准备新来源组确认；先不夸大机制或AI优势。
- 只修某种问法/某类题，或收益伴明显损伤：明确适用范围，下一轮若继续须针对具体反例；不能称通用修复。
- 激活干预有用而静态编辑无用：记录可实现性缺口；不能用激活结果替代WSP成果。
- 工具正常但额度内没有有效候选：两条线分别结算有限搜索阴性，保留轨迹；不自动扩大网络范围、预算或换题救结果。

新来源组和图片/素材审计可以在工程准备时开始，但不为凑组数制造新题。开发可行性探索不必等终验数据全齐；**发表意义上的修复泛化结论必须等新数据确认**。旧H重新拆分或改写都不变成新独立材料。确认样本量按拟主张的效果与损伤精度单独设计，当前不编造可用数量。

##### 6. 自查：设计层面通过，执行合同尚待完成

设计卡：主线是AI反馈驱动的稀疏权重修补；增量是从行为缺口进入真实可修性探索；证据来自S0原始成对结果，反证包括B错误异质、C问法依赖和强提示副作用；操作为同一W0上分支独立静态差分；估计对象为固定输入下联合正确率及分格损伤；开发、旧H回归和未来新确认分开；成本建议与待冻结项见§5；预算耗尽或无合格候选允许结束。

| 项 | 判定与理由 |
|---|---|
| C01 | 通过：保留B/C与AI自主修补主线，未转成单纯探针或定位论文。 |
| C02 | 通过：将增加静态稀疏可修性的实测证据或有限搜索失败证据，不重复S0。 |
| C03 | 通过：复用完整raw、评分、D输入、v6开放工具；未声称已有内部激活或真实编辑验收。 |
| C04 | 通过：猜想与反证同列，行为缺口不证明信息完整、局部可修或AI必成功。 |
| C05 | 通过：静态权重与临时激活诊断分开；AI选位置和数值，服务记录每次实际操作。 |
| C06 | 通过：协议固定，下游正常响应；重载去hook，估计整体补丁效果。 |
| C07 | 通过：记录绑定权重和全网后果，不把少量编辑称局部功能独立；合并须另测。 |
| C08 | 通过：补丁有效不证明唯一病因、原生路径或AI比脚本好；后者需要另做公平搜索比较。 |
| C09 | 通过：B可能是识别/关系/筛选/计数，C可能多原因；诊断预测由AI逐轮提出并接受反例。 |
| C10 | 通过：以完整自然回答、组级联合与分格修对/改错为核心，探针和logit不替代。 |
| C11 | 通过：工程失败先修，有限搜索阴性另报；15pp只保留历史判定，不当科学边界。 |
| C12 | 通过（阶段计划）：先CPU整理；真实编辑新增运行有明确用途。预算建议已列，数值执行合同未完成不得启动。 |
| C13 | 通过：来源组为单位，旧H已见；新确认尚缺；版本、失败与所有候选保留。 |
| C14 | 通过：收益、损伤、静态实现失败、无候选有不同后续；不因两线有价值就无限追加。 |

相关历史错误：E02不锁层；E03标量数与扰动分报；E10完整答案；E11探针阴性不等于无信息；E12差距缩小不抵消控制损伤；E16保留阴性；E20不强行唯一病因；E21没有更新近邻查重，不宣称新颖性；E22旧H不能作新终验；E23本记录为同一助手自查；E24不等完整机制才试改；E25先做有限探索，不展开所有消融。E01按本WSP主线检查；其余E04–E09、E13–E15、E17–E19、E26涉及特定历史状态拆换，本轮无该操作，其归因边界由C06–C08覆盖。

与前版比较：删除“至多一个优先对象”；保留开放位置/计算与逐轮反馈；S0从计划变成事实；新增C视觉问法保护，拒绝单向压低图像影响；明确旧H只作已见回归；新确认从探索启动前置条件改为泛化结论前置条件，避免阻碍有界开发探索。

反方检查及修正：

1. “B是看到结果才放宽。”保留原判定且不改p值；另记用户选择继续，后续只作探索，不包装为原预注册通过。
2. “AI只记住D或学答案偏好。”全D含成功、问法与顺序，双向分格报告；这仍不能排除开发过拟合，所以新确认前不作泛化结论。
3. “C常识涨分只是忽略图。”视觉/通常联合评价，并逐格保留T1损伤；不能只汇总掩盖此反例。
4. “自由选点仍然被旧选择器锁成T0。”发现v6主条件选择与新目标可能不一致；加入离线映射检查和修改要求，未核实前不启动。
5. “同样2小时就能比较哪条线更可修。”不成立：数据规模、诊断成本不同；初轮等资源只用于公平启动机会，不用于普遍可修性排名。
6. “工程全过等于研究者已会自主发现。”不成立：合成脚本和真实工程只证明接线，真正研究者的逐轮轨迹与候选效果才是后续证据。

复查结论：阶段推进逻辑通过；未完成数值执行合同、真实编辑工程验收、新确认材料和近邻比较。自查不等于独立审查。本次不触发新GPU或研究者调用；已结束的S0监控保持停止。下一步优先完成§3第一步及真实验收所需配置，再提交可执行的有限探索合同。


##### 2026-11-05 后续授权：v8 双卡各30轮

用户已撤销上述旧两小时硬截止，确认 B/GPU0、C/GPU1 各完成30轮不同非零候选修补＋完整开发评估；诊断不计轮。当前权威入口、批量数值边界、失败记录和自查见[WSP-VLM v8](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05/README.md)。旧预算和队列仅保留历史，不用于当前调度。

---

### 原件 4：WSP-VLM v7：真实反馈接入、工程验收与B/C开放探索

原路径：`experiments/wsp-vlm-open-repair-v7-2026-11-05/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7-2026-11-05/README.zh-CN.md) · [单独阅读副本](../library/7377b17fb846f114.md)；SHA-256：`7377b17fb846f1144eaa7f36add658e9afb893e0106a284baa7b63d9ab7976b0`。

---

#### WSP-VLM v7：真实反馈接入、工程验收与B/C开放探索

2026-11-05。用户在[双线推进方案](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/wsp-vlm-bc-continuation-v1-2026-11-05.zh-CN.md)后回复“同意，推进吧”；本轮按[数值合同与自查](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7-2026-11-05/PLAN.zh-CN.md)执行。v6及S0原始记录保留，本目录是新版本。

**本次归档时：工程验收已完成；B自主研究会话已启动，C串行排队。还没有可报告的WSP修复结果。** 运行时状态以本机`sequence.json`、`search-{B,C}/conversation/`和远端同版本external目录的`state.json`为准；本段是启动快照，不冒充实时状态。

##### 已完成

- 真实D反馈：B58来源组/464输入/89个去重原图或预览文件；C64组/2560输入/256文件。全部原版raw回答、正确标签、成功和失败、两种问法及提示、C两种顺序均接入。逐ID和图片hash核验，见`audit/development_export.json`；大图片包留external，未复制上游素材到Git。
- 候选选择改为普通提示、来源组等权的多问法/顺序联合正确率；保护项逐提示×问法×顺序×条件检查。C目标为反事实通常/视觉双正确，五条件仍全部保护与报告。不能靠单一问法涨分或控制退化被选为最佳。
- 29项离线检查通过，包括“总体均分不变但T1变坏必须拒绝”、来源组等权，以及已验证原版缓存复用不新增前向。见`audit/offline_tests.log`、`audit/offline_receipt.json`。
- 真实工程：48条既有D输入的回答、生成token、输入token hash、模板hash及图像尺寸完全匹配；固定模型实际模块/权重绑定核对；内部读数与直接计算一致；三个工程标量修改、异常回滚和模型重载后结果一致；隔离CPU变量可持续，不能访问凭据、GPU、网络或项目封存资料。
- 本机研究者三轮实测：图片中的左右颜色正确、续接记住nonce、续接再次收到图片。已核对同一session、CLI原始事件和usage；不把图片探测称作研究能力评估。

工程三次尝试累计84.411秒，预算3600秒；前两次7.816秒、28.610秒失败，第三次47.985秒通过，全部保留。第三次48条重放＋4次修改/恢复生成＋2次有效完整内部前向，另有1次在前向前拒绝的无效模块测试；两次真实模型加载。第二次失败也曾加载模型，不能说全部失败都在加载前。研究者网络测试与CPU准备另记墙钟，未与GPU时间混加。工程测试固定选三个组件的各一标量仅为数值验收，没有按任务分数挑选，未提供给研究者作为选点答案。

##### 修复过的工程问题

1. 服务器bubblewrap 0.3.1不支持`--clearenv`：改为子进程`env={}`，保留网络/文件系统/GPU隔离，真实隔离检查通过。未使用不隔离回退。
2. 固定Qwen3-VL输出头与词嵌入共享权重，空别名表使初始化拒绝：加入`lm_head.weight → model.language_model.embed_tokens.weight`，用实际存储指针、形状和回滚检查核验。没有改变模型原始值。
3. 服务器研究者CLI路由发现超时：保留失败事件，改用旧数学实验的本机研究者＋SSH远端观察者方式；没有复制登录凭据。
4. 本机探测相对路径被CLI工作目录重复拼接：改为绝对路径。第一次在模型调用前退出；第二次图片输出正确但带围栏，检查器接受围栏中的原始JSON并从已完成第一轮续接，不重复收费调用该轮。

5. B首轮发现开发包由同步保留了UID 501和0600权限，隔离工具失去特权后无法直接读bundle；研究者已自行改用evidence接口继续。观察者将B/C四个开发JSON改为0644，内容hash不变，隔离读取复验通过（`audit/permission_fix.json`）。未重启搜索或补回已用预算；以后传输同类包需显式保证隔离内可读。

##### 现在如何运行

本机`launch_sequence.py`一次性按B→C启动；`remote_search.py`复用旧数学的持久SSH JSONL模式，`controller.py`直接复用旧数学动作解析器并持续交回真实反馈。研究者为gpt-6-astra/max，经已有ChatGPT登录；参数选择和非梯度修改代码全部由研究者逐轮生成，不存在预写神经元排名或固定修补算子。CLI文字/图片和resume依据[官方非交互说明](https://learn.chatgpt.com/docs/non-interactive-mode)并以本机实测为准。

远端Python为`/workspace/acupuncture/.venv-bench/bin/python`，固定模型位于同项目external下无符号链接的hash验证视图。独立NumPy工具环境为`.venv-wsp-v7-cpu`，任意AI Python仅在bubblewrap中执行。原版D预测经真实输入一致性验收后由观察者导入缓存；包中的原始`diagnostic_only`标记保留其导出时身份，升为原版比较缓存由`seed_screen_baseline`显式完成并标记`reused_original_screen/new_model_calls=0`。不能由AI提交自造基线。

每条线墙钟7200秒、100轮/100操作等上限见配置和PLAN；先到任一额度停止，AI等待也计入。B/C分别从W0开始，不共用补丁；同一GPU串行。传输不确定时停止并查持久回执，不盲目重放。`sequence.json`已存在时拒绝重复启动；技术错误停止队列待修，正常完成/诚实无补丁停止才继续C。正式加载、样本、token、CPU工具时间和所有失败计账。

研究者费用按ChatGPT订阅调用/usage记录，美元成本未知，无API fallback或购买额度；观察token限额允许最后一轮usage超出，硬界限是轮数和墙钟。候选实际存储可能大于稀疏支持数，提交前检查完整存储所需空间并至少保留20GiB；每30分钟在本聊天汇报磁盘、进度和预算剩余/ETA，不推送其他消息渠道。

##### 结果与结论边界

这里只完成了从S0到S1/S2的工程通路，尚无内部失败机制或修复有效性结论。研究者已开始读取真实数据、提出诊断和使用工具；是否找得到有净收益的静态稀疏候选，要看后续逐轮记录。

旧H不提供给本次研究者，也不再作为新独立确认；未来新来源组终验、近邻方法比较、同预算脚本搜索、独立搜索重复尚未完成。预算内没有有效补丁是允许结果，不因为B/C都值得研究就自动加码。不得把工程三个标量或原版筛查结果称为WSP补丁成绩。

工程原始JSON/日志、CLI对话与usage均归档；`.npy`整张原始权重拷贝不进入Git，工程差分由记录的三个张量各第一个标量`+0.125`并按BF16量化可重建。正式搜索产物在结束后另归档；此启动交付不声称搜索完成。自查是同一执行助手完成，不是独立审查。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [audit/engineering-r1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7-2026-11-05/audit/engineering-r1/receipt.json) | {"scope": "engineering_only", "status": "failed"} | {} |
| [audit/engineering-r2/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7-2026-11-05/audit/engineering-r2/receipt.json) | {"scope": "engineering_only", "status": "failed"} | {} |
| [audit/engineering-r3/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7-2026-11-05/audit/engineering-r3/receipt.json) | {"scope": "engineering_only", "status": "complete"} | {} |
| [audit/offline_receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7-2026-11-05/audit/offline_receipt.json) | {"model_calls": 0} | {} |
| [audit/researcher-probe-local-r2/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7-2026-11-05/audit/researcher-probe-local-r2/receipt.json) | {} | {} |
| [audit/researcher-probe-local-r2/turn1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7-2026-11-05/audit/researcher-probe-local-r2/turn1/receipt.json) | {} | {} |
| [audit/researcher-probe-local-r2/turn2/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7-2026-11-05/audit/researcher-probe-local-r2/turn2/receipt.json) | {} | {} |
| [audit/researcher-probe-local-r2/turn3/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7-2026-11-05/audit/researcher-probe-local-r2/turn3/receipt.json) | {} | {} |

## 全部原始资产入口

本目录在固定提交下共有107个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/137-wsp-vlm-open-repair-v7-2026-11-05.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7-2026-11-05)。未复制模型权重、环境或凭据。
