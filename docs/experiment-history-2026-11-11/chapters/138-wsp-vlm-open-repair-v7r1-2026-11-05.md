# 138．v7r1连接恢复与批内权重复用

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-05；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

等待旧远端动作完成后续接同一研究者，改为持久inbox及同批一次载入候选，保持输入、补丁、解码和评分不变。

**实际过程、结果与后来更正**

保留SSH断开、后台管道超时、r2脱离启动、原预算不重置及真实批一致性验收记录。恢复工程和有效候选轮数分开，不把重连算新实验收益。

**来源身份**：`wsp-vlm-open-repair-v7r1-2026-11-05`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：原始文档

原路径：`experiments/wsp-vlm-open-repair-v7r1-2026-11-05/RESEARCHER.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7r1-2026-11-05/RESEARCHER.md) · [单独阅读副本](../library/c1ce04c7e05a3933.md)；SHA-256：`c1ce04c7e05a39338489e06cd775b544bad1cebc7e9dc60f24f5ec94dfbcafd5`。

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

### 原件 2：v7r1：连接中断恢复与批内权重复用

原路径：`experiments/wsp-vlm-open-repair-v7r1-2026-11-05/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7r1-2026-11-05/README.zh-CN.md) · [单独阅读副本](../library/3c38e752200751e0.md)；SHA-256：`3c38e752200751e0f46c888a326d91a5bfe101ec6f5d93670cf7d8d10520dafc`。

---

#### v7r1：连接中断恢复与批内权重复用

**13:18追加：当前权威队列改为`sequence-r2.json`，入口`recovery_r2.py`。** 首版恢复启动的shell后台任务仍持有SSH管道，30秒超时导致本机队列退出；远端broker PID 1711513实际仍在等待，已核实并复用，不重启。r2只修启动/核对：C用Python Popen显式断开stdin/stdout/stderr并新建会话。真实短CPU脱离启动检查4.95秒返回，子进程持续15秒；无模型或研究者调用。原预算未重置。首版失败栈/队列及r2检查见audit。批处理的真实数值验收仍待原评估完成，尚未声称通过。

2026-11-05 12:53启动快照。继承v7、B/C推进方案及用户“bug直接修复”授权。**B原有候选评估仍在运行；新恢复进程只等待其锁和完整回执，不重复原调用。C尚未启动。** 当前队列以本目录sequence.json为准；旧v7/sequence.json保留其stopped_on_error历史状态。

##### 发现与处理

- 本机SSH在约31分钟后报Connection reset by peer，研究者流程停止；远端原评估仍由timeout保护运行。保留原stderr、异常栈、请求、停止回执于audit。没有将通信失败解释为候选失败。
- 原实现每道题都校验、读取、装载及恢复同一整张候选张量；AI只改一个标量时也会反复处理整张词嵌入矩阵。本次不是增加修补算子：候选张量、输入、生成、评分均不变，只将同一批评价包在一次candidate上下文内。内层同候选复用，跨候选嵌套拒绝，整批异常仍恢复W0。
- 新broker使用持久inbox/action/response。短SSH仅传输JSON和读取状态，网络断开不结束远端计算。同ID/同内容可确认投递，已执行回执直接读取，未完成动作不重放。
- B等待旧观察者锁释放且每个已登记动作都有回执，然后加载同一配置、状态、候选与预算。研究者续接原thread和累计token/轮数，从第19轮继续；告知Python变量因重启丢失，已有work、提案和测量文件保留。**没有提供新的选点或修改配方。**
- B继续沿用约14:00的原始截止，不补回断线/等待时间。C在B退出后独立最多2小时，从W0开始；技术异常仍停止队列，正常结束或预算耗尽继续C。

##### 验收状态

29项本机离线测试通过，增加同候选嵌套、跨候选拒绝及恢复检查。初次本机缺复制的config.template.json（1项错误）、服务器缺原数学解析器文件（4项错误）均保留日志；补齐本机模板后通过。服务器不运行研究者解析器，实际解析仍在本机。

**真实批处理一致性尚待执行。** B原完整评估结束并释放锁后，新broker先用该候选前两条既有输出比较自然生成token、输入/模板hash和图像尺寸，再检查异常退出后的W0自然输出；共3次工程前向，费用计入剩余共享工程预算并记录batch_acceptance.json。通过后才允许新的研究者动作，C也检查这一验收和源文件hash。不把离线通过冒充真实通过，不把等待状态叫作修复成功。

##### 自查

这是实现修复，未修改原实验设计、标签、终点、保护界限或预算，仍沿用v7 PLAN及C01–C14。关键复查：C03保留原版本/raw；C05/C06候选值完全相同、生成等价须实测；C08不作能力/机制结论；C11先验收再继续；C12保留原开始时间、失败费用及全部额度；C13未给研究者H；C14不扩预算。自查不是独立审查。

反方风险：连接恢复不能猜测动作是否完成，因此锁未释放或缺回执时只等；Python变量重建由AI自行处理；批内复用可能掩盖回滚错误，因此真实同候选输出和异常W0检查为硬门槛；完整评估若耗尽B预算，允许B无可用结果，不能重置计时。尚未证明补丁有效，也未进行独立泛化确认。

启动：本机recovery.py；远端broker.py；原run目录和配置仍在v7，所有原始回答持续写原目录。代码及恢复证据单独放v7r1，未替换正在运行的v7源文件。以后监控同时读两版本的队列和回执。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [audit/detached-launch-check-r2.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7r1-2026-11-05/audit/detached-launch-check-r2.json) | {} | {} |
| [audit/launch-r2.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7r1-2026-11-05/audit/launch-r2.json) | {} | {"time_unix": "2026-11-05T05:17:14.496964+00:00"} |
| [audit/offline_receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7r1-2026-11-05/audit/offline_receipt.json) | {"model_calls": 0} | {"time_unix": "2026-11-05T04:54:16.822580+00:00"} |
| [launch_receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7r1-2026-11-05/launch_receipt.json) | {} | {"time_unix": "2026-11-05T04:52:18.880090+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有42个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/138-wsp-vlm-open-repair-v7r1-2026-11-05.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7r1-2026-11-05)。未复制模型权重、环境或凭据。
