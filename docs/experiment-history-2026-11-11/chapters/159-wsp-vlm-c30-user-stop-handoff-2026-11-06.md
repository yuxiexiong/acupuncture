# 159．Qwen C30用户收尾与队列交接

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-06；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

核对已完成30候选且无待处理动作后，依用户指令停止C，修正Gemma仍错误等待C50的门禁。

**实际过程、结果与后来更正**

C开发58.203125%→60.9375%，修28错10；报告未接受、候选未冻结，以用户允许的收尾状态退出。停止没有新增模型调用，也没有C31–50。后续Gemma开始真实工程，不把工程算搜索轮次。

**来源身份**：`wsp-vlm-c30-user-stop-handoff-2026-11-06`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。

## 逐轮候选完整账目

- [Qwen-v9-C逐轮目的、改动和结果](../rounds/Qwen-v9-C.md)


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：原始文档

原路径：`experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/after/v8/RESEARCHER.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/after/v8/RESEARCHER.md) · [单独阅读副本](../library/cef2b488ee50fc09.md)；SHA-256：`cef2b488ee50fc097ae9291c61f90ffd7411d2463b97f128b776d742eeecbb2c`。

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
relative to W0, across any legitimate parameter locations. There is no session wall cutoff. Each branch allows 30 distinct nonzero
full-development candidate evaluations, 2000 actions/researcher turns, and
50 million cumulative researcher tokens. Budget exhaustion or a real blocker
must be reported honestly.
Your persistent CPU workspace has NumPy only; use the metered observer for every
model forward. Select your own observations and edit computation. You may change
your hypothesis using feedback; an engineering error is not a task failure.

Model: google/gemma-3-4b-it, starting from fresh W0. Use Gemma runtime_catalog, not Qwen layer recipes. Native images are 896x896, 256 visual tokens; image_grid_thw is empty. The original input image is authoritative; preview images retain historical Qwen preview provenance and are not Gemma processor outputs. Previous Qwen predictions are excluded. Inspect ARTIFACTS/baseline.json for this model’s full W0 results. Each distinct nonzero candidate fully evaluated on D counts, including no-gain and protection-failing candidates; diagnostics and cached repeats do not count. Candidate storage is lossless sparse absolute FP32 values reconstructed against W0; inference uses BF16. Run storage cap 12 GiB, filesystem reserve 20 GiB; retain failures and stop on exhaustion.

---

### 原件 2：原始文档

原路径：`experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/after/v9/RESEARCHER.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/after/v9/RESEARCHER.md) · [单独阅读副本](../library/d6df541f03271be4.md)；SHA-256：`d6df541f03271be4433be905683a637cf42a5e26115049d4a19b300f53619e2a`。

---

You are the researcher, using gpt-6-astra with max reasoning. Your task is to
improve this VLM by understanding a concrete failure and making targeted static
weight changes. The human fixes data access, evaluation and resources, but has
NOT supplied a failure mechanism, layer, neuron list, direction or edit formula.
You must choose and revise these using actual evidence. No successful repair is
required. Never substitute superficial parameter sweeps for the requested study.

WHAT COUNTS
Diagnose failures and comparable successes. Identify candidate neurons, heads,
directions or circuits. State a falsifiable behavioral prediction before editing.
Test the prediction and several meaningful strengths. Distinguish correlation,
causal intervention, a useful static patch, and generalization. A direction read
from hidden states is not automatically a cause. If claiming direction AND channel
selection matter, use suitable matched random-direction and random-channel tests;
otherwise limit your claim. Include actual BF16 support/norm and control damage.
Direct weight probes can help localization without a complete mechanism first,
but label them diagnostic. Final evidence must explain why the chosen components
and operation help, or honestly say evidence is incomplete/negative. A numeric
score improvement alone is not a mechanism finding.

RULES
- Start from W0. No prior patch, layer recipe or original-author solution is given.
- Embeddings/tied output and final decoder norm are excluded. Multiplying an
  entire tensor by a scalar is excluded, including individual norm weights.
- All other real model parameter locations are available; MLP is not mandated.
  Compute your own non-gradient edits using NumPy. No model training/autograd,
  unmetered inference, altered evaluation, gold in model prompts, external routing,
  or changing model/tokenizer/decoding/architecture. Report any supervised fitting.
- Static candidates must run ordinary complete generation with no diagnostic hooks.
  Existing development data are seen: do not claim independent generalization.
- Do not assume a single shared failure, or name a module's function from its ID.

WORKING LOOP
1. Read complete W0 answers and raw success/failure examples. Group actual errors
   and choose a concrete, consequential failure. Keep normal successes as controls.
2. Build comparable contrasts. Preserve task meaning and gold when comparing
   success/failure rewordings. Comparing different correct tasks can encode a
   legitimate task switch; answer position, word identity and difficulty confound
   raw activation differences. Test competing interpretations across examples.
3. Measure internal vectors in candidate modules, usually before the answer.
   Inspect relevant projection columns, candidate directional writes and their
   input-dependent activations when appropriate. Architecture and linear algebra
   are tools, not discoveries. Probe a reasonable range rather than only 8 arbitrary
   coordinates. AI selects locations and coordinates, never a precomputed ranking.
4. Record prediction, evidence and intended control; calculate and commit an edit.
   Test predicted behavioral effects, dose and counterexamples. Complete fixed-D
   evaluation is used for every candidate considered for best. Read repaired AND
   worsened IDs, not just summary scores. Retain invalidated hypotheses.
5. Within 30 distinct nonzero full-D candidate evaluations, reserve meaningful
   tests for your best explanation; do not spend all rounds on tiny scale tweaks.
   Measurements, diagnostic generations and subset probes are separately budgeted,
   not counted as full candidate rounds. Controls and failed full evaluations count.
   Aim for 30 substantive rounds, but stop honestly for a real blocker/exhaustion;
   never fabricate hypotheses or duplicate weights to reach a number.
6. At the round cap synthesize a mechanism_report about the selected best candidate,
   including controls, negative findings and limits, then freeze. The service only
   validates evidence references/completeness; it does not certify your causal story.

TOOLS
Explain evidence, next action and predicted observation, then return exactly ONE
fenced `python` or `forward` block. Python persists on CPU and has NumPy as np.
`catalog()`, NAMES, `load_original(name)`, `load(name)`, `save_edit(name,array)`,
`drop_edit(name)`, `edited()` read/stage existing parameters. `EVIDENCE` is the
allowed bundle directory; `ARTIFACTS` contains complete returned JSON and NPY arrays.
Use np.load(..., allow_pickle=False). No framework/model execution in Python.
Save relevant computed directions, channel lists, rankings and comparisons in
/work with sufficient provenance; summarize paths in your report. Array saving
uses exact absolute FP32 values against W0, preserving effective BF16 weights.

Forward operations:
- status; evidence (optional ids); image(request_id,kind=input|preview);
  catalog; runtime_catalog. The latter lists real runtime modules/shapes.
- measure(candidate,ids,spec): one teacher-forced forward per ID, no generation.
  spec={"layers":[AI-chosen decoder layer indices],"token_positions":"last_prompt"}
  conveniently captures each layer's residual output and MLP down_proj INPUT.
  `token_positions` can be explicit nonnegative positions; inspect returned actual
  token IDs/prompt length/image positions. Layer indices are zero-based actual
  module indices. Continuations are explicitly teacher-forced, not natural traces.
  Generic spec.capture entries support module, where=input|kwargs|output, path,
  optional token_positions or flat_indices. Do not use decoder token axes on vision.
  spec.continuation and score_token_ids are available. Spec.interventions supports
  module/where/path/explicit flat_indices/values and operation=add|replace|scale;
  these only affect this forward and never become a static candidate.
  Returned captures include array_file relative to ARTIFACTS, SHA256, original
  shape, selected_shape and token_positions. Load arrays in Python, not via text.
- diagnose: same fields/readout as measure, PLUS ordinary free generation for
  each input. Costs TWO forwards per ID. Readout is teacher-forced; generation
  has no temporary hooks and is scored as diagnostic only. With a continuation,
  readout sees it but generation starts from the unchanged user prompt.
  Both measure/diagnose accept optional text_overrides mapping existing input IDs
  to new diagnostic user questions. Original images remain fixed, full-D evaluation
  unchanged. These custom questions are diagnostics, not independently graded tests.
- commit(parent,rationale,evidence): commit immutable candidate. Parent=current.
  evidence must contain strings failure_behavior, component_hypothesis,
  expected_change, dose, control_plan; contrast_ids (>=2 allowed input IDs),
  measurement_actions (previous successful action IDs), role=targeted|diagnostic|control.
  A targeted role requires actual recorded internal captures. Diagnostic/control
  edits may precede localization; they never count as validated mechanism evidence.
- checkout(candidate): revert current; staging clears, Python variables do not.
- evaluate(candidate, optional ids): W0/parent/candidate paired full generation.
  Omit ids for fixed full-D evaluation and automatic behavior-only best selection.
- accept(candidate): same frozen behavioral score/protection rule.
- mechanism_report(report): strings candidate, failure_behavior, internal_evidence,
  causal_tests, counterevidence, scope, verdict; action_ids cite successful records.
  The candidate must be the actual selected best before freeze. Negative or
  unsupported verdicts are legitimate. Discuss any divergence from your predictions.
- freeze: save best plus report, end. stop(reason): honest early stop. Plain final
  reply also ends the session. artifact(name,offset,length<=12000) pages saved JSON.

EVALUATION AND RESOURCES
B is total/spatially conditioned counts; C is visual/usual size under original,
counterfactual and no-image conditions. These descriptions do not prescribe causes.
Read EVIDENCE/bundle.json. Fixed full D: B 58 source groups/464 inputs, C 64/2560.
Ordinary-prompt joint correctness is the selection endpoint, averaged over wording/
order then source groups. Per wording/order/prompt cell max loss=.035 vs W0;
format/truncation each<=.01. Ties prefer fewer effective changed scalars. Report all
conditions, overall answers, repaired/worsened IDs and C five-way correctness.
Max effective scalar support: temporary4,000,000/final1,000,000 relative to W0,
not parent; tied storage counts once. 30 unique full candidate rounds each branch;
2000 actions/researcher turns; CPU36000s; researcher50M tokens; no session wall cap.
Each diagnostic batch<=64 IDs; each forward<=2M captured/intervened elements.
All calls, failures, model load/idle time and storage count. Run allocation12GiB,
filesystem reserve20GiB. Do not download/copy models or accumulate dense snapshots.
Stop instead of deleting evidence or expanding budgets. This is development-method
research, not an unseen-model or independent-test success claim.

Model: google/gemma-3-4b-it, starting from fresh W0. Use Gemma runtime_catalog, not Qwen layer recipes. Native images are 896x896, 256 visual tokens; image_grid_thw is empty. The original input image is authoritative; preview images retain historical Qwen preview provenance and are not Gemma processor outputs. Previous Qwen predictions are excluded. Inspect ARTIFACTS/baseline.json for this model’s full W0 results. Each distinct nonzero candidate fully evaluated on D counts, including no-gain and protection-failing candidates; diagnostics and cached repeats do not count. Candidate storage is lossless sparse absolute FP32 values reconstructed against W0; inference uses BF16. Run storage cap 12 GiB, filesystem reserve 20 GiB; retain failures and stop on exhaustion.

---

### 原件 3：Qwen C30按用户要求结束与Gemma队列交接

原路径：`experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/REPORT.zh-CN.md) · [单独阅读副本](../library/613c10a8745bf8ba.md)；SHA-256：`613c10a8745bf8ba9877c520ae13d87658b38696bff51823676c08bdf84a3921`。

---

#### Qwen C30按用户要求结束与Gemma队列交接

2026-11-06。用户明确要求：C若已完成30组，就直接结束并撤出，把资源交给下一个队列。该指示覆盖此前必须等待研究者报告、冻结的收尾要求，不授权C31–50。

##### 已执行

- 核对C恰好30个完整候选、没有未决动作，使用原服务的`stop`接口发送唯一动作`user-stop-C30-20261106`。停止成功，原PID1852016退出，两卡短暂均为3MiB显存；没有杀进程替代停止，也没有新增C模型调用。
- 保留实际最佳`c-9652d71dc3f8671029f03a284ca51fb4e013a51510c29e99d4fe3ae3424dd53d`，开发分数60.9375%，W0为58.203125%，修对28、改错10。状态标明研究结束，但报告未接受、候选未冻结，不伪造成功收尾或独立泛化。
- B50保持结束及原交付身份，未重启或修改B。
- 发现Gemma r02排队门禁仍要求Qwen B/C都达到50轮；C早已改为30，即使正常退出也会一直等待。最小修复只允许：C累计恰好30、研究结束且有本次明确用户停止动作成功收据时释放该依赖；B仍须50轮完成。Gemma v9仍等v8两组完整结束。
- 修复前源码和清单完整保留于`before/`，修复后于`after/`，差异见两个queue.patch。v8/v9各6项无模型测试通过，涵盖C29、C未结束、缺停止收据和B不足50仍应等待。
- 4个远端旧排队器均先核实只有waiting状态、无engineering/search目录，无任何Gemma模型动作；仅替换这些等待进程，旧PID和状态归档。本地4个原控制器短暂停住以避免交接窗口误报，随即继续；没有重新创建研究者线程或重放动作。
- Gemma v8 B/C已分别进入GPU0/1工程验收和有界batch校准，实测GPU利用率100%/97%，PID2108588/2108587为工程子进程；v9 B/C保持waiting_gemma_v8。工程通过才进入正式搜索，不把当前工程计入30轮。

##### 原因与边界

C的第166回合机制报告缺少candidate字段而被拒；第167回合出现429/容量错误，没有成功usage回执。此前恢复合同禁止自动重复容量失败，所以没有重试；但未及时处理长时间占卡及排队门禁与新目标不一致的问题，导致后续任务一直等待。此次按新的明确指示结束C，不继续修补它的研究者报告。

本次只改变结束授权与调度交接，不改变Gemma数据、模型、评分、候选预算、修改范围、批量校准规则或工程验收门槛。Gemma原有独立授权见original-v8/v9-queue-authorization.json；旧2B/8B及旧Gemma队列仍不恢复。失败数据、动作及不确定结果全部保留。

C正式累计目标样本80,956、目标token10,844,818、Python94.223秒；研究者已知累计27,088,282 token，143/167失败用量未知。停止动作新增模型调用0，停止本身约0.0014秒。当前研究者报告/冻结未完成是用户允许的结束状态，不再阻挡资源交接。

##### 证据与后续

[C停止动作](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/C-stop-action/response.json)、[实际最终状态](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/C-final-state.json)、[排队替换收据](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/queue-restart-receipt.json)、[下一队列实际占卡](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/next-queue-live.json)、[CPU测试](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/queue-tests.json)、[完整C研究者轨迹](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/C-researcher-trace.tar.gz)。C全部远端文件保留原路径，完整本地备份位于`external/wsp-vlm-mechanism-repair-v9-2026-11-05/archive-C30-user-stop-2026-11-06/`，文件来源及SHA见C-remote-files.json。

半小时心跳已更新为Gemma四组队列巡检，不再等待或恢复Qwen C。工程状态、完整轮次、异常、资源、用量和实测ETA继续按阶段汇报。

##### 归档核验结果

[离线核验](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/C-verification.json)通过：10,311个远端文件、1,997,427,301字节逐项SHA一致；30个不同非零候选、31次完整评价、79,360条原始回答重新评分一致。1,824个研究者文件逐字节核对，含失败143/167；完整轨迹和[C评价及候选](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/C-evaluations-and-candidates.json.gz)已纳入交付。新增C模型调用为0，没有以离线核验补造机制报告或冻结。

---

### 原件 4：Gemma 3 4B：v8/v9 两版 B/C 各30轮

原路径：`experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/after/v8/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/after/v8/README.zh-CN.md) · [单独阅读副本](../library/71131dafcd6876bd.md)；SHA-256：`71131dafcd6876bd04abca1d029f9fcfe27a8982f3e4c45a16d128973510fab7`。

---

#### Gemma 3 4B：v8/v9 两版 B/C 各30轮

用户2026-11-05确认两模型×两版×B/C各30轮后，本次明确“那就先Gemma吧。你直接把Gemma上卡排队。”本次范围仅Gemma四组，共120个不同非零候选的完整开发评估；Qwen2B/8B不启动。此前Gemma旧C50轮队列和暂停标记保留。

执行状态以 `audit/activation.json` 和远端各组 `queue-status.json` 为准；排队、CPU检查、真实GPU验收、正式基线及搜索完成分别记录。逻辑自查为同一助手完成，不是独立审查。

##### 设计卡

1. **主线与问题。** AI自主依据VLM失败选择非梯度稀疏静态修补。将Qwen3-VL-4B上两套已实际执行的方法分别移到Gemma，检查其开发收益、损伤与内部诊断证据是否仍出现。不是缓存写入—读取线，不借用该线证据。
2. **增量。** 跨家族检验原方法的适用范围；不把多一个模型或30次候选本身叫机制发现。已有Qwen结果不能提供Gemma的原版失败、合法收益或机制证据。
3. **来源与反例。** 复用 `wsp-vlm-open-repair-v8-2026-11-05/PLAN.zh-CN.md`、`wsp-vlm-mechanism-repair-v9-2026-11-05/PLAN.zh-CN.md`、旧Gemma适配和CPU收据、固定B/C开发数据。Qwen v8 B联合指标改善但整体净收益较小、粗调未触及多数错误；v9内部诊断不保证胜过开放修改。Gemma可能无改善或损伤过大。
4. **操作。** 固定 `google/gemma-3-4b-it` revision `093f9f388b31de276ce2de164bdc2081324b9767`，原始官方权重、BF16、SDPA、greedy、128新token、batch64。Gemma原生模板和896×896单图/256视觉tokens；不用Qwen模板、坐标或权重补丁。每组独立W0、研究者上下文、候选、预算和目录。两版不串接权重：v9仍从W0开始。
5. **固定与响应。** B58来源组/464输入；C64组/2560输入。四组复用相应原图、标签、顺序、评分和逐格保护；移除旧Qwen预测。Gold不进入目标模型提示。修改后下游正常生成。临时内部hook仅为诊断；最终候选是普通推理可加载的静态补丁。
6. **比较与判读。** 每组以本模型同批量完整W0为对照，按普通提示joint及既有保护选优，同时报告全输入正确率、修对/改错、各条件和完整回答。有效改善只支持本模型本开发任务的可修补性；无改善/保护失败保留。工程失败不是科学阴性。跨模型或v8/v9分数差不能唯一归因于架构/内部诊断：模板、基线、搜索轨迹与合法修改范围均不同。正式比较30轮机会须对照Qwen前30轮原规则保留状态，不能与50轮最优混为公平比较。
7. **范围与成本。** 四组各30个不同非零候选完成全部D计轮，失败改善/未过保护亦计；诊断、部分评估、原版和重复权重不计。每组2000动作/研究者轮次、36000 CPU秒、50M研究者累计tokens；B样本/前向上限69600、C384000，token上限分别293990400/1622016000。无总墙钟截止，单次研究者900秒、CPU300秒。四组纯W0+30完整候选为187488条自然生成，非总耗时预测；工程、诊断与失败另计。每组工程两次加载，v8各132生成+2内部前向，v9各133生成+5内部前向；正式服务另加载一次。研究者沿用既有ChatGPT登录的gpt-6-astra/max，无API回退。
8. **退出。** 每组30轮后按版本原冻结规则结束；v9先记录机制报告再冻结。早停、预算耗尽、工程/控制器失败保留证据，不自动重试、不追加轮数。v8未完整结束时v9不自动绕过。Qwen2B须另按届时磁盘和用户指令推进。

##### 两版区别与必要适配

- **v8：** 保留开放合法参数修改范围、原内部measure接口和行为选优；允许原版中的词嵌入/输出和统一缩放。30轮自动冻结。
- **v9：** 保留禁止embedding/绑定输出/最终decoder norm/整张张量统一缩放、内部向量/diagnose接口、事前预测和对照引用、独立机制报告。修正Gemma旧checkpoint名称下最终norm与输出排除映射，不能因名称不同绕过限制。
- **共同工程变化：** 两版使用既有精确稀疏绝对FP32值存储，重建后检查完整内容hash及实际BF16参数；不保存有舍入误差的算术差分。v8只移植存储/磁盘检查，不新增v9诊断能力或修改限制。源文件与适配来源见 `source-provenance.json`、`source-manifest.json`、`reuse.json`。
- **图像身份：** `input`是原图，历史`preview`仍具有Qwen预览来源标记，不能称Gemma预处理输出；CPU/GPU验收均另核原生Gemma实际输入。

##### 排队、资源与验收

四组远端目录：`/workspace/acupuncture/external/wsp-vlm-gemma3-{v8,v9}-2026-11-05-r02/{B,C}/`。对应代码为同名 `experiments/` 目录。两版分别执行 `queue_run.py --task B/C --server`；本机去掉`--server`为独立研究控制器。启动只执行一次，不重用不明状态目录。

先等待已有Qwen4B v9 B/C及其已授权50轮续跑完整结束，避免30轮重载空档被新任务抢卡；然后v8 B/C竞争空卡，v8两组完整结束后v9 B/C进入。取得共享GPU文件锁后再次确认无计算进程、显存<128MiB、利用率0。工程验收在隔离子进程执行，成功后新进程阶段加载同配置做本组完整W0；不抢占、不杀旧任务。现有任务若异常停滞，Gemma保持等待，不能自行恢复或结束旧任务。

每组运行目录12GiB，全盘至少20GiB；工程/临时合计按6GiB预留，四组48+6+20=74GiB，再为现有Qwen任务约21GiB可能增长预留，总约95GiB。23:17工作盘实测144.076GiB，足够本轮；权重已下载且共享，不复制四套。单组领取GPU前至少38GiB可用，搜索每动作检查存储。此为预算，不保证任意研究者工作文件都能容纳；超限停，不删除证据。

CPU：离线回归、原生处理器有图/无图、真实meta架构、共享权重映射及官方文件hash。GPU：严格checkpoint加载、固定batch64重复、单题/批量输入身份、原生processor输入一致、静态三个标量的稀疏重建/回滚/重载、logit与hook数值。v9追加按模块名对应完整向量的直接hook核对、禁止动作检查、二进制capture服务读回。研究者图像/持久会话传输复用未改动controller的既有真实收据并核hash；不冒充本轮新测。新验收绑定任务、合同、证据、权重和本版代码hash，未通过不得搜索。

##### C01–C14 自查（规范v1）

| 项 | 判定与理由 |
|---|---|
| C01 | 通过：保留AI自主静态修补B/C，跨模型不换为缓存/EOS课题。 |
| C02 | 通过：新增Gemma上收益/代价与内部证据的适用边界，不以数量冒充认识。 |
| C03 | 通过：原v8/v9合同、代码、数据、旧Gemma适配及收据均复用并冻结。 |
| C04 | 通过：Qwen粗调有限收益、v9可能无优势、Gemma可能失败均明确。 |
| C05 | 通过：各组独立W0静态修改；临时诊断与最终补丁分离。 |
| C06 | 通过：任务/评分固定，Gemma采用自己原生输入，下游自然响应。 |
| C07 | 通过：共享LM头按真实alias合一；禁止动作同时覆盖checkpoint与runtime名。 |
| C08 | 通过：开发修补、内部证据、泛化分开；两版/跨模型差不是单因素因果效果。 |
| C09 | 通过：研究者选择失败诊断及预测，v9保留原事前证据要求，不预写位置。 |
| C10 | 通过：完整D自然回答与损伤为终点，诊断logit不替代答案。 |
| C11 | 通过：CPU/GPU实现失败与合法无改善分开；保留失败，不自动救结果。 |
| C12 | 通过：旧数据不能提供Gemma回答；只跑授权四组，模型共享、诊断有界、验收计账。 |
| C13 | 通过：独立目录与研究者会话、源/hash、原回答/失败/预算保留；原D仍是开发。 |
| C14 | 通过：正负结果约束跨家族适用性；120轮为上限，不自动扩2B或加轮。 |

历史错误：E01主线稳定；E02不移植Qwen层号；E03相同绝对支持非相同有效扰动；E04内部算术不当发现；E10/E11答案/读数分开；E12保护不能消除全部损伤；E14不混必要充分；E16保留阴性；E20两版差异非互斥原因；E21方法复用不称首创；E22同源开发非独立确认，重复问法非独立样本；E23自查/验收/排队/完成分开；E24允许有界证据；E25不扩矩阵。E05–E09、E13、E15、E17–E19、E26的缓存拆换/形成读取操作本轮不涉及，输入与路径的一般风险由C05–C08覆盖。

反方检查与处理：①两版成功仍可能是同D选优→仅报开发结果，后续未见材料仍缺；②Gemma失败可能源于输入适配→先核原生processor、模型/数值与回滚，失败停线；③把v9存储移到v8可能偷带限制/工具→v8保留原service/backend，只有存储guard和候选内容hash更新，合同targeted=false；④共享权重旧名称可绕过排除→CPU测试和真实工程均核Gemma canonical名；⑤排队能抢30→50重载空档→先检查旧任务完成50；⑥两版从前版补丁继续会混淆→每组W0及研究者会话独立；⑦30轮对50轮不公平→对齐30轮机会，另列历史50；⑧磁盘预算不是运行保证→按实测检查并保留超限失败。

设计结论：在上述方法复用和开发证据范围内通过；同一助手自查，非独立审查。当前用户已明确授权排队及上卡；GPU验收和结果分别以实际收据为准。本轮未扩大Qwen2B/8B授权。

##### r02 启动修正

首次四个本机控制器并发SSH握手时，服务器关闭两条连接，两组按失败停线；另外两组仍在等旧Qwen。核对全部四组均无engineering/search目录、无Gemma模型/GPU/研究者调用后，仅停止本任务的等待进程。首次代码、日志和状态保留原目录。本r02使用新代码/输出/启动身份，串行SSH握手并复用连接；只对只读查询和同ID幂等状态/请求写入最多重试3次，不重试研究者付费调用、不重放目标模型动作。新增测试证明重试的命令/载荷身份不变。模型、数据、预算、两版差别和排队顺序不变；C05/C08/C11/C13及E23重新检查通过，逻辑自查不是独立审查。

##### 单卡效率更新（用户追加指示，2026-11-05）

用户要求查阅既有单卡优化研究、尽可能提高GPU使用效率。本节覆盖上文固定batch64及其固定工程调用计数；数据/解码/两版修改范围/30轮不变。依据：v7r2 `batch_trials.json` 的Qwen C实测32/64/128/256分别43.97/45.94/46.48/45.22输入/秒；v9耗时审计中生成阶段可达99%–100%利用率，但研究者回合占60%–67%、工具往返约20%。这些不是Gemma实测，不能直接承诺同速或全程满卡。

**冻结的有界校准：** v8 B/C各自在同一张空闲H20、原版W0上，用按condition/template/arm/order轮转取得的256条开发输入（不按正确率筛选），32条预热，然后batch32/64/128/256各两遍；每次CUDA同步后计包括编码/拷贝的端到端时间、输入/秒、峰值allocated/reserved显存、跨批量token差异和同批量重复一致性。上档前按既有峰值外推、12GiB余量及90%总显存保护判断是否跳过；未预料的OOM或同批量不重复视为工程失败，停线，不悄悄降配置继续。最多2080条额外工程生成/任务，共4160，不计搜索轮次。选择重复一致且保留至少12GiB显存、达到实测最快吞吐95%的最小批量；不按任务正确率选择。

B/C分别冻结所选批量；v9同任务复用v8选择，不重复调参。两版都从同一Gemma W0开始，以选定批量完整重测自身基线，验收同时核对两版同制度W0答案。批量可能改变答案，故保留差异而不把它当修补收益；与旧Qwen比较须注明各模型执行制度，不能声称纯架构效果。

工程重复验证的样本数n=max(64,所选batch)。v8每组生成2n+4+校准样本、内部前向6次；v9每组生成2n+5、内部前向9次；模型加载仍工程2次、正式1次/组。所有原始工程输出保留。每组验收收据保存实际计数、所选batch并绑定；启动器读取selected-config，不沿用旧base里的64。

**减少实际空转：** 已加入实验专用SSH复用、串行握手；在复用连接上响应轮询从5秒降到1秒。所有读/写均为持久不可变动作ID或幂等状态，不自动重试研究者调用。同一次measure/diagnose请求在候选上下文内完成全部逐样本前向，只装载一次静态候选、末尾回滚；每条前向/捕获仍按原顺序、batch1、原数值设置执行。CPU检查上下文进入/退出次数，真实工程另核两个输入的单独/合并候选上下文读数完全相等、结束后W0逐值恢复；不声称已测得节省量。未更换推理后端、量化、Astra模型/推理档位或研究策略，不添加无研究用途的计算填空。

**C01–C14复查：** C01通过：效率服务原四组修补；C02通过：科学增量仍为跨家族适用性，性能测量只是工程；C03通过：使用原批量实测和耗时账本；C04通过：更大batch未必更快且Gemma结果未知；C05通过：只冻结执行批量并合并相同候选的装卸；C06通过：任务/生成固定、同批量W0比较，诊断逐样本不变；C07通过：绑定权重和回滚保持；C08通过：性能/开发收益/机制证据分开，不称纯架构因果；C09通过：吞吐/显存/重复性决定配置，不由任务分数选；C10通过：正式终点仍完整D自然回答；C11通过：OOM/重复性/数值等价失败停线且留原件；C12通过：仅两任务有界校准，v9复用，不循环扩大batch范围；C13通过：原始输出、调用数、选定配置与代码hash冻结；C14通过：速度无改进仍可采用安全配置，性能不决定扩研究预算。

新增历史错误复查：E03显存占用不等于效率、支持数不等于扰动；E10吞吐不替代科学指标；E19数值等价验收非发现；E22工程样本不是新独立研究样本；E23校准待运行不写成实测结果；E25不引入无限batch/架构调参。其余沿上文，缓存专用项仍不适用。

反方：①挑最快可能挑到数值有利批量→选择完全不看正确率，保留输出差异且重测同制度W0；②Gemma与Qwen吞吐相同是假设→新模型实测、无速度承诺；③合并上下文会遗留hook/候选→每次measure仍自行finally移除hook，真实逐值/回滚验收；④研究者等待仍会使GPU空闲→如实记录，不能靠无用计算或改变研究策略宣称全程100%。逻辑自查通过；此更新尚无Gemma GPU性能结果。r02此前仅完成CPU准备、尚未启动队列，旧r02校准前代码封存在audit/pre-throughput-source.tar.gz；最终冻结源码以更新后的source-manifest为准。

**实际排队核验：** 2026-11-05T23:58:56.489065+08:00，两组远端队列与本地控制器均存活；状态waiting_existing_qwen4b / waiting_server，Gemma GPU验收/性能校准/正式搜索尚未开始。最终本地及服务器离线测试39项全过，原生处理器/meta CPU检查通过；工作盘可用约143.94GiB。见[audit/activation.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/after/v8/audit/activation.json)。

---

### 原件 5：Gemma 3 4B v9：内部诊断 B/C 各30轮

原路径：`experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/after/v9/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/after/v9/README.zh-CN.md) · [单独阅读副本](../library/0084c320cbde25eb.md)；SHA-256：`0084c320cbde25eb8db0052b0bc828099e7d22c8da11b42062aa4a098299c96e`。

---

#### Gemma 3 4B v9：内部诊断 B/C 各30轮

本目录是Gemma四组任务中的v9两组；v8两组完整结束后排队领取空闲GPU，各自从原版W0和独立研究者会话开始。

共同合同、用户授权、模型/数据身份、C01–C14及反方自查、存储预算和运行顺序见[完整设计与队列说明](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/after/wsp-vlm-gemma3-v8-2026-11-05-r02/README.zh-CN.md)。保留v9禁止词嵌入/绑定输出/最终norm/整张张量缩放、内部向量捕获、预测与对照引用及机制报告要求；不加载v8补丁，不共享其研究者对话。

状态以 `audit/activation.json`、远端 `external/wsp-vlm-gemma3-v9-2026-11-05-r02/{B,C}/queue-status.json` 和逐组工程收据为准。CPU通过不等于GPU通过或科学结果。研究者自身解释不是独立机制审查。

##### r02 启动修正

首次四个本机控制器并发SSH握手时，服务器关闭两条连接，两组按失败停线；另外两组仍在等旧Qwen。核对全部四组均无engineering/search目录、无Gemma模型/GPU/研究者调用后，仅停止本任务的等待进程。首次代码、日志和状态保留原目录。本r02使用新代码/输出/启动身份，串行SSH握手并复用连接；只对只读查询和同ID幂等状态/请求写入最多重试3次，不重试研究者付费调用、不重放目标模型动作。新增测试证明重试的命令/载荷身份不变。模型、数据、预算、两版差别和排队顺序不变；C05/C08/C11/C13及E23重新检查通过，逻辑自查不是独立审查。

##### 单卡效率更新（用户追加指示，2026-11-05）

用户要求查阅既有单卡优化研究、尽可能提高GPU使用效率。本节覆盖上文固定batch64及其固定工程调用计数；数据/解码/两版修改范围/30轮不变。依据：v7r2 `batch_trials.json` 的Qwen C实测32/64/128/256分别43.97/45.94/46.48/45.22输入/秒；v9耗时审计中生成阶段可达99%–100%利用率，但研究者回合占60%–67%、工具往返约20%。这些不是Gemma实测，不能直接承诺同速或全程满卡。

**冻结的有界校准：** v8 B/C各自在同一张空闲H20、原版W0上，用按condition/template/arm/order轮转取得的256条开发输入（不按正确率筛选），32条预热，然后batch32/64/128/256各两遍；每次CUDA同步后计包括编码/拷贝的端到端时间、输入/秒、峰值allocated/reserved显存、跨批量token差异和同批量重复一致性。上档前按既有峰值外推、12GiB余量及90%总显存保护判断是否跳过；未预料的OOM或同批量不重复视为工程失败，停线，不悄悄降配置继续。最多2080条额外工程生成/任务，共4160，不计搜索轮次。选择重复一致且保留至少12GiB显存、达到实测最快吞吐95%的最小批量；不按任务正确率选择。

B/C分别冻结所选批量；v9同任务复用v8选择，不重复调参。两版都从同一Gemma W0开始，以选定批量完整重测自身基线，验收同时核对两版同制度W0答案。批量可能改变答案，故保留差异而不把它当修补收益；与旧Qwen比较须注明各模型执行制度，不能声称纯架构效果。

工程重复验证的样本数n=max(64,所选batch)。v8每组生成2n+4+校准样本、内部前向6次；v9每组生成2n+5、内部前向9次；模型加载仍工程2次、正式1次/组。所有原始工程输出保留。每组验收收据保存实际计数、所选batch并绑定；启动器读取selected-config，不沿用旧base里的64。

**减少实际空转：** 已加入实验专用SSH复用、串行握手；在复用连接上响应轮询从5秒降到1秒。所有读/写均为持久不可变动作ID或幂等状态，不自动重试研究者调用。同一次measure/diagnose请求在候选上下文内完成全部逐样本前向，只装载一次静态候选、末尾回滚；每条前向/捕获仍按原顺序、batch1、原数值设置执行。CPU检查上下文进入/退出次数，真实工程另核两个输入的单独/合并候选上下文读数完全相等、结束后W0逐值恢复；不声称已测得节省量。未更换推理后端、量化、Astra模型/推理档位或研究策略，不添加无研究用途的计算填空。

**C01–C14复查：** C01通过：效率服务原四组修补；C02通过：科学增量仍为跨家族适用性，性能测量只是工程；C03通过：使用原批量实测和耗时账本；C04通过：更大batch未必更快且Gemma结果未知；C05通过：只冻结执行批量并合并相同候选的装卸；C06通过：任务/生成固定、同批量W0比较，诊断逐样本不变；C07通过：绑定权重和回滚保持；C08通过：性能/开发收益/机制证据分开，不称纯架构因果；C09通过：吞吐/显存/重复性决定配置，不由任务分数选；C10通过：正式终点仍完整D自然回答；C11通过：OOM/重复性/数值等价失败停线且留原件；C12通过：仅两任务有界校准，v9复用，不循环扩大batch范围；C13通过：原始输出、调用数、选定配置与代码hash冻结；C14通过：速度无改进仍可采用安全配置，性能不决定扩研究预算。

新增历史错误复查：E03显存占用不等于效率、支持数不等于扰动；E10吞吐不替代科学指标；E19数值等价验收非发现；E22工程样本不是新独立研究样本；E23校准待运行不写成实测结果；E25不引入无限batch/架构调参。其余沿上文，缓存专用项仍不适用。

反方：①挑最快可能挑到数值有利批量→选择完全不看正确率，保留输出差异且重测同制度W0；②Gemma与Qwen吞吐相同是假设→新模型实测、无速度承诺；③合并上下文会遗留hook/候选→每次measure仍自行finally移除hook，真实逐值/回滚验收；④研究者等待仍会使GPU空闲→如实记录，不能靠无用计算或改变研究策略宣称全程100%。逻辑自查通过；此更新尚无Gemma GPU性能结果。r02此前仅完成CPU准备、尚未启动队列，旧r02校准前代码封存在audit/pre-throughput-source.tar.gz；最终冻结源码以更新后的source-manifest为准。

**实际排队核验：** 2026-11-05T23:58:56.489065+08:00，两组远端队列与本地控制器均存活；状态waiting_existing_qwen4b / waiting_server，Gemma GPU验收/性能校准/正式搜索尚未开始。最终本地及服务器离线测试41项全过，原生处理器/meta CPU检查通过；工作盘可用约143.94GiB。见[audit/activation.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/after/v9/audit/activation.json)。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [C-verification.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/C-verification.json) | {"model_calls": 0} | {} |
| [queue-before/v8-B/controller-status.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/queue-before/v8-B/controller-status.json) | {"stage": "waiting_server"} | {"time_unix": "2026-11-05T15:58:11.339511+00:00"} |
| [queue-before/v8-B/queue-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/queue-before/v8-B/queue-launch.json) | {} | {"time_unix": "2026-11-05T15:57:15.891464+00:00"} |
| [queue-before/v8-C/controller-status.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/queue-before/v8-C/controller-status.json) | {"stage": "waiting_server"} | {"time_unix": "2026-11-05T15:58:13.364059+00:00"} |
| [queue-before/v8-C/queue-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/queue-before/v8-C/queue-launch.json) | {} | {"time_unix": "2026-11-05T15:57:15.891818+00:00"} |
| [queue-before/v9-B/controller-status.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/queue-before/v9-B/controller-status.json) | {"stage": "waiting_server"} | {"time_unix": "2026-11-05T15:58:15.387948+00:00"} |
| [queue-before/v9-B/queue-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/queue-before/v9-B/queue-launch.json) | {} | {"time_unix": "2026-11-05T15:57:15.892116+00:00"} |
| [queue-before/v9-C/controller-status.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/queue-before/v9-C/controller-status.json) | {"stage": "waiting_server"} | {"time_unix": "2026-11-05T15:58:17.376022+00:00"} |
| [queue-before/v9-C/queue-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/queue-before/v9-C/queue-launch.json) | {} | {"time_unix": "2026-11-05T15:57:15.892394+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有58个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/159-wsp-vlm-c30-user-stop-handoff-2026-11-06.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06)。未复制模型权重、环境或凭据。
