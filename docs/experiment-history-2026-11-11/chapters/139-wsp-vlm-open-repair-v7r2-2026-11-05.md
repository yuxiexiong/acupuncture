# 139．v7r2后续恢复版本

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-05；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

保存前轮恢复后的研究者约束、实现与回执。

**实际过程、结果与后来更正**

本目录缺独立顶层结果报告；其文件与原调用状态完整列出，和v7/v8共同追溯，不凭目录存在补造一组完成成绩。

**来源身份**：`wsp-vlm-open-repair-v7r2-2026-11-05`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：原始文档

原路径：`experiments/wsp-vlm-open-repair-v7r2-2026-11-05/RESEARCHER.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7r2-2026-11-05/RESEARCHER.md) · [单独阅读副本](../library/c1ce04c7e05a3933.md)；SHA-256：`c1ce04c7e05a39338489e06cd775b544bad1cebc7e9dc60f24f5ec94dfbcafd5`。

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


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [benchmark-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7r2-2026-11-05/benchmark-launch.json) | {} | {"time_unix": "2026-11-05T05:47:50.223887+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有28个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/139-wsp-vlm-open-repair-v7r2-2026-11-05.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v7r2-2026-11-05)。未复制模型权重、环境或凭据。
