# 140．WSP VLM v8双卡真实批量搜索

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-05；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

改为真实batch64，在B58来源464输入、C64来源2560输入上开放修补；最初各30轮，之后有独立累计50轮授权。

**实际过程、结果与后来更正**

30轮阶段与50轮续接保留各自身份。最终完成结果见v8x50；每个候选相对W0的静态修改、保护失败与选优规则均保留，不只保存最后赢家。

**来源身份**：`wsp-vlm-open-repair-v8-2026-11-05`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：v8：双H20、真实批量、各30轮修补评估

原路径：`experiments/wsp-vlm-open-repair-v8-2026-11-05/PLAN.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05/PLAN.zh-CN.md) · [单独阅读副本](../library/66b9c32cf1adc31f.md)；SHA-256：`66b9c32cf1adc31fda11169db0e54118070c27735395be7e92436cb4b6b042f5`。

---

#### v8：双H20、真实批量、各30轮修补评估

用户2026-11-05明确授权：C用物理GPU1，成功后B在GPU0复用单卡高批量；取消两卡硬GPU总时限；用户确认“30轮修补＋完整评估”，诊断不计轮。本计划覆盖此前串行/两小时安排，保留旧配置、运行、失败和费用记录。

##### 设计卡与固定比较

主问题不变：研究者AI能否依据VLM真实失败和内部反馈，自选位置与非梯度修改，用稀疏静态权重修补提高任务表现并控制损伤。B是空间条件计数（D58来源组、464输入），C是反事实图干扰通常常识（D64组、2560输入）。模型、revision、BF16、SDPA、greedy、128生成上限、处理器、题目、标签、评分、逐格保护和支持数上限沿用v7。

B/GPU0与C/GPU1独立并行，常规推理先采用batch64。C在256条工程输入上测试batch4–256，与既有逐题token、输入/模板hash和图像尺寸均一致；batch64达到约45.9条/秒，接近batch128约46.5条/秒，batch256反而约45.2条/秒。选择接近最快档且更小的64，不以填满显存为目标，至少预留12GiB。

B在原版/旧补丁各464条中，batch64相对逐题分别有3/2条答案差异；不能称完全等价，不能把差异计为WSP收益。使用batch64自身重复性和输入身份核对；通过才进入新阶段。两条线均在新run完整重测W0，再以相同固定顺序/批量评估所有候选。新的主要比较仅在同一批量制度内。此前B首补丁及S0均保留历史角色，不当新独立确认。

##### AI循环与30轮计数

AI读完整D成功/失败→提出假设→自选诊断、层/神经元、非梯度修改→提交不可变补丁→完整D自然生成→获得修对/改错、指标和保护反馈→下一轮。没有预写选层或神经元排名。观察者只执行输入、计费、静态稀疏校验及冻结的选择规则。

每条线目标30轮。一次不同的、非零权重补丁完成全部D评估计1轮；诊断、局部评价、失败/中断、缓存重复、仅改变说明但权重相同均不计。权重身份按实际张量内容hash去重。完整评估没有涨分或未过保护也计轮，避免只数成功。第30轮后观察者按既有目标/保护选择最佳并冻结；W0仍可为最佳。旧慢速B轮次不计入v8。达到30轮只意味着开发搜索完成，不意味着成功或泛化。

没有总墙钟/GPU超时，配置wall_seconds=null，服务器无timeout包裹、本机父进程无运行截止。保留单次研究者请求900秒、单次CPU工具300秒作为挂起检测，不是总GPU时间额度。每任务2000动作/研究者轮次、累计CPU36000秒、研究者5000万token观察上限；目标样本上限为5×30×完整D大小，token保守预留按每样本4224计算。这些防失控额度不把诊断算为修补轮；若先触及它们或真实阻塞，必须报告少于30轮的实际状态，不能宣称完成或自动加码。美元费用未知，沿用ChatGPT登录，无API fallback。

研究者CLI返回thread累计usage，v8保留raw并按相邻累计值差计账；旧运行重复累计触发早停的记录保留，不改原receipt。目标前向样本、基线、工程重放、失败分别记录。

##### 自查与相对上一版变化

C01：主问题仍是AI开放稀疏修补，吞吐优化服务于更多有效迭代。C02：实质增量是30个完整候选的反馈链，不用诊断调用数量替代。C03：复用D、模型、已有答案和控制器；新版本保留旧run。C04：负收益和控制损伤允许，不能为凑30伪造收益。C05：实际操作仍为静态权重；批量只改变执行制度，另建同制度基线。C06：输入和评分固定，下游正常生成；批内一次装载末尾回滚。C07：绑定权重按唯一标量计；不宣称少坐标就是小功能变化。C08：仅开发修补效应，不作机制唯一性或泛化论断。C09：AI逐轮自述预测，观察者不提供配方。C10：完整答案和逐格联合指标，非logit替代。C11：工程失败/批量数值差异/科学负结果分开。C12：用户新授权取消总时限，按30轮；先实测吞吐并留显存余量。C13：新W0基线、源hash、实际批量、旧H已见边界及失败raw全部保留。C14：最终报告有效轮数、最佳补丁、损伤及剩余确认缺口，不因30轮用尽自动扩规模。

历史重点：E02不固定两层；E03同时记录标量数和范数；E10不把内部得分当正确答案；E11不以探针阴性淘汰；E12保护每种问法/顺序而非仅总体；E16保留无效补丁；E22来源组计统计单位；E23同助手自查不冒充独立审查；E24不等完整机制才试改；E25不顺带开展新模型或LoRA。其余缓存拆换专用错误本轮无对应操作。

反方检查：大批量可能改变少数答案，B已经出现，所以必须新基线且限制结论；高显存占用未必高吞吐，实测256不比64快；30次反复看D可能过拟合，必须保留未来独立新来源组终验；重复权重可刷轮数，按内容hash去重测试；无总时限可能在网络/工具处卡住，保留单次超时、持久请求身份、进程存活检查及每30分钟监控，不能不明状态重放。

逻辑自查通过；30项离线回归（含唯一完整轮计数与无总时限）通过；真实批量测试及B同批量复验另由回执说明。方案/代码交付不等于30轮结果，尚无独立审查或终验。

---

### 原件 2：原始文档

原路径：`experiments/wsp-vlm-open-repair-v8-2026-11-05/RESEARCHER.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05/RESEARCHER.md) · [单独阅读副本](../library/c1ce04c7e05a3933.md)；SHA-256：`c1ce04c7e05a39338489e06cd775b544bad1cebc7e9dc60f24f5ec94dfbcafd5`。

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

### 原件 3：WSP-VLM v8：双卡各30轮开放修补

原路径：`experiments/wsp-vlm-open-repair-v8-2026-11-05/README.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05/README.md) · [单独阅读副本](../library/9e70af35b0ca889e.md)；SHA-256：`9e70af35b0ca889e7802070ab8fd6d254a247675eda504c7871726e15dc81422`。

---

#### WSP-VLM v8：双卡各30轮开放修补

此版覆盖旧v7/v7r1串行两小时截止安排；旧记录保留，不能按旧队列重启。用户确认一次不同的非零权重修补＋完整开发评估为一轮，B、C各30轮；诊断和重复不计。总GPU/墙钟硬截止已撤销。

- [方案、自查与计数规则](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05/PLAN.zh-CN.md)
- [B真实批量重复验收](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05/remote-audit/batch-acceptance-B.json)
- [C真实批量验收](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05/batch-acceptance-C.json)；[吞吐测试](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7r2-2026-11-05/batch_trials.json)
- [30项离线验收](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05/offline-r3.log)；初次失败及修复日志同时保留。
- `run_rounds.py --task B/C` 是当前入口，`round_broker.py` 是远端观察者，`monitor.py` 只读监控。两任务独立，不使用复制的历史 `run_c.py`。

##### 已观察状态（2026-11-05 14:19 北京时间快照）

C物理GPU1、B物理GPU0，batch64。C已完成1/30轮，B完成完整W0基线、0/30轮。B远端PID1741153，C1736582；启动/监督回执为实际身份来源。B首次启动因SSH握手断开失败，失败文件保留在failed-B-launch-01，核对后恢复，未重复启动远端模型。

C批量4至256的256条工程输入均与逐题生成token一致；64为45.94条/秒，128为46.48、256为45.22，选64保留显存余量。B batch64原版/旧补丁各464输入约40.32/38.98秒，两次重复完全一致、输入hash一致；但相对旧逐题运行有3/2条答案变化。因此两线都完整重测相同batch64的W0，所有修补只与这个同制度基线比较。不能把批量制度带来的差异当作WSP收益。

远端run：`/workspace/acupuncture/external/wsp-vlm-open-repair-v8-2026-11-05/{B,C}`。原模型、数据来源仍在v7 external目录；不提交模型权重或凭据。工程逐题raw无损打包在remote-audit/B-batch-raw.tar.gz和v7r2/batch-raw.tar.gz，旁有逐文件SHA256清单。搜索中的raw持续写在远端，结束后单独归档。

##### 边界与下一步

AI自主诊断、选点和非梯度修改；未固定层/神经元配方。完整无收益或未过保护的候选仍计轮；重复权重不计。第30轮自动按冻结规则选最佳，W0可胜出。仅看到开发集收益，不构成独立确认、通用机制或泛化证明；旧H已经看过，只是回归面板。30轮之后仍缺新的独立来源组确认和最终补丁重载验收。

每30分钟监控磁盘、GPU、完整轮数、修对/改错和ETA；当前轮数少，完成时间未知。保留单次工具超时及动作/样本/token防失控额度，触及额度需报告真实阻塞，不能把不足30轮报成完成。方案自查不是独立审查。


##### 15:04 后续：条件满足，总目标提高至各50轮

按最近5个完整轮间隔估算，B/C的30轮预计分别15:49/16:38，均早于用户规定的17:23，因此已启动[50轮自动续接](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8x50-2026-11-05/README.md)。当前v8正常跑到30保存并退出，等待器随后恢复同研究者thread和run继续31–50；不热改、不打断当前评估。总目标50已授权并排队，真实续接尚待30轮边界回执。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [launch-B.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05/launch-B.json) | {} | {"time_unix": "2026-11-05T06:17:07.962746+00:00"} |
| [launch-C.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05/launch-C.json) | {} | {"time_unix": "2026-11-05T06:05:48.591311+00:00"} |
| [remote-audit/launch-B.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05/remote-audit/launch-B.json) | {} | {"time_unix": "2026-11-05T06:17:07.962746+00:00"} |
| [remote-audit/launch-C.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05/remote-audit/launch-C.json) | {} | {"time_unix": "2026-11-05T06:05:48.591311+00:00"} |
| [remote-audit/verify-B-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05/remote-audit/verify-B-launch.json) | {} | {"time_unix": "2026-11-05T05:59:58.167100+00:00"} |
| [remote-audit/verify-B-repeat-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05/remote-audit/verify-B-repeat-launch.json) | {} | {"time_unix": "2026-11-05T06:07:27.947108+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有65个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/140-wsp-vlm-open-repair-v8-2026-11-05.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8-2026-11-05)。未复制模型权重、环境或凭据。
