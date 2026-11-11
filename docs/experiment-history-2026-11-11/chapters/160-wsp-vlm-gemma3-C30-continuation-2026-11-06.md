# 160．Gemma v8 C早停后的30轮接续

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-06；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

原C在4轮停止，按用户明确要求在同线程保留既有候选与评分，接续至累计30个不同非零候选；不重跑W0和已完成评价。

**实际过程、结果与后来更正**

恢复时区分旧finished收据和新控制器身份，首个接续研究者回合35成功。此项是执行接续记录，最终C30结果在后续Gemma完整交付条目；没有另起一批30轮。

**来源身份**：`wsp-vlm-gemma3-C30-continuation-2026-11-06`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：原始文档

原路径：`experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/v9-instructions-after/RESEARCHER.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/v9-instructions-after/RESEARCHER.md) · [单独阅读副本](../library/3e05c4da7b3ffa97.md)；SHA-256：`3e05c4da7b3ffa97785dae85f490dc06a2a5767e6c2fb864951a78543991e5db`。

---

LATEST USER EXECUTION REQUIREMENT (2026-11-06): Complete TOTAL 30 distinct nonzero full-development candidate evaluations. Negative or inconclusive results are acceptable, but do not voluntarily stop before 30 merely because tested edits have not improved scores. This supersedes any voluntary early-stop language below. Preserve failures and all cumulative budgets; report real engineering or budget blockers honestly. Do not claim success, replay unknown actions, or change scientific conditions to meet the count. After 30 submit the honest mechanism report and freeze under the original rules; no additional repair candidates.

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

### 原件 2：原始文档

原路径：`experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/v9-instructions-before/RESEARCHER.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/v9-instructions-before/RESEARCHER.md) · [单独阅读副本](../library/d6df541f03271be4.md)；SHA-256：`d6df541f03271be4433be905683a637cf42a5e26115049d4a19b300f53619e2a`。

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

### 原件 3：Gemma v8 C继续至30轮与统一研究者停止要求

原路径：`experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/REPORT.zh-CN.md) · [单独阅读副本](../library/e79dfd4f6738e95a.md)；SHA-256：`e79dfd4f6738e95ab29979f3dbe707b40535230b20fccf116545b4cb270e70fb`。

---

#### Gemma v8 C继续至30轮与统一研究者停止要求

2026-11-06 07:40巡检发现：Gemma v8 C在turn34、4/30主动提交阴性结果并停止，预算未耗尽，没有工程阻碍。旧研究者指令允许阴性早停，和用户当前“四组各30轮、继续跑、同类工程问题及时修复”的要求冲突。按现有授权修正并接续，不再次询问同一类指令冲突；这不涉及已经按用户要求结束的Qwen C。

##### 实测进度与科学边界

B已从4推进至12/30。当前所选R10主分数17.2414%，W0为16.3793%，提高0.8621个百分点；但全体正确率从43.5345%降到43.1034%，修对1、改错3。通过原保护门槛仅说明允许的开发指标权衡，不是全面改善或独立泛化。其他候选的主分数改善若触发保护失败仍不选。

C前4轮主分数34.7656%、32.4219%、32.8125%、33.5938%，W0为33.9844%；第一候选提升但两个保护格各降4.69个百分点，其余未改善。实际最佳仍是W0、全体正确率79.1406%。两个相反projector gain都修复同一C-007视觉错误，削弱简单单调图像强度解释；不是已识别的通用修复机制。

##### 已执行的最小恢复

复用上一轮已验证B续跑器，单独版本化为resume_C.py，仅更换任务C、旧停止turn34、下一turn35、原PID2108564及GPU1。正在运行的B和已验收v8引擎源码不变。1个合法边界与8个拒绝边界在本地和远端均通过，测试新增模型调用0。

恢复前核对4个不同完整候选、34个完整动作、成功stop、W0已恢复、5份完整评价缓存hash和相同合同/协议/模型/数据/批量32；确认无pending/partial动作、旧服务退出、GPU1空闲。原state/config/identity及队列、控制器状态保存到checkpoint-user-continue-round4，不覆盖历史停止记录。

同Astra线程01a1addf-9ba6-77b2-8466-d863db04b647从turn35接续剩余26轮，承接2,056,821 token和原目标样本12,802；数据、候选、评分缓存、累计预算不清零，不重算W0、不重放历史动作。Python内存变量重建，原工作文件保留并告知研究者。后端按首次新前向加载，ready时实际加载0，不能把对象构造当模型装载。

新服务PID2138641、本地控制器63951，以C-continuation-status和实际PID为准。旧controller的finished/receipt是4轮早停历史，不能当30轮完成。

##### 防止后续重复

v9两组仍未开始工程或Astra调用，已在RESEARCHER.md顶部加入最新明确指令：必须完成累计30个不同非零候选的完整评价，阴性结果可以保留，但不能只因暂未改善自愿提前结束；真实工程或预算阻碍仍需报告，不能强行改科学条件或重放不明动作。更新source-manifest并保存修改前后文件。v9机制报告/冻结规则保留；达到30后的收尾失败按用户要求保存证据并释放资源，不再无限阻塞后续。

半小时心跳已记录C新身份与旧状态边界，v9仍按前序结束核验后运行。未新增模型、轮次或科学假设，未恢复任何旧Qwen队列。

实际恢复验收：同线程turn35已完成且工具反馈成功，研究者累计token为2,165,057；对应原始事件、收据和反馈见C-resume-turn35。

后续R13更新（取代上文R10作为当前最佳）：主分数20.6897%，相对W0增加4.3103个百分点；全体正确率45.4741%，修对19、改错10。仅将绑定embedding/lm_head的数字0行236771乘1.5，改变2,560个标量。它是输出校准的开发线索，不是MLP机制修复或独立泛化证据。完整W0与候选回答及补丁见B-round13-evidence.json.gz。

---

### 原件 4：Gemma r02 08:10巡检

原路径：`experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/heartbeat-0810/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/heartbeat-0810/REPORT.zh-CN.md) · [单独阅读副本](../library/e5597685f40dbdcc.md)；SHA-256：`e5597685f40dbdcc854a1621f57044a64a1791ddb441fb160a647f918c42f9c5`。

---

#### Gemma r02 08:10巡检

2026-11-06北京时间08:10状态快照，随后核验B turn91已成功。四个远端服务/等待器及本地控制器命令均核对；本次不改运行源码、科学条件或队列，v8/v9 source-manifest逐文件一致。

| 组别 | 完整轮次及较07:45增量 | W0→实际最佳主分数 | W0→最佳全体正确率 | 修对/改错 |
|---|---|---|---|---|
| v8 B | 18/30，+5 | 16.3793%→21.5517% | 43.5345%→46.5517% | 26/12 |
| v8 C | 8/30，+4 | 33.9844%→33.9844% | 79.1406%→79.1406% | 0/0，所选仍W0 |
| v9 B/C | 各0/30 | 未运行 | 未运行 | 等待v8科学评价结束 |

B实际最佳为R17，候选c-b77d500cbd51c5a107504d55674393523ea267e4155035cce6e273965d942795：数字0绑定embedding/输出行×1.50，再加视觉桥mm_soft_emb_norm有效gain×0.90；其他decoder norm恢复W0，实际改变3707个BF16标量。比R13进一步改善，仍属开发集适应，不能称独立泛化或MLP机制修复。完整W0/最佳回答及补丁清单见best-evidence.json.gz。

C新增R5–R8为attention/MLP全层残差gain的正反向试验，主分数分别34.375%、31.640625%、34.375%、30.859375%，都触发逐格保护拒绝；不能只报其中34.375%而当作可接受收益。B累计5次measure、C3次measure，均不计修补轮或直接证明机制。B最新用8张预定图像测量视觉桥256×1152输出，预选144个高/低空间均值能量比例通道做数量配对比较；能量未匹配，尚无该新候选完整结果，不能预称方向特异性成立。

B turn90计算完成后误向只读/artifacts写诊断文件，失败收据完整保留，模型评价未发生、内存未重置。turn91已将已有诊断完整打印入持久动作回执并成功暂存后续编辑；没有放宽只读证据保护、重放原动作或重新计算模型评价。本次核对证实问题已由研究者当场处理，控制器没有停线。B/C均未冻结，仍在搜索；v8不要求v9格式机制报告，v9尚未开始。

##### 耗时与ETA

同机请求/响应mtime差减远端elapsed_seconds计算工具等待。统计B turn71–90（R13后）、C turn36–50（恢复后），原始数值见timing.json。Astra整回合包含API排队、上下文处理和输出，不是纯思考；类别计时不是GPU占用时间。

| 阶段 | B秒 | C秒 |
|---|---:|---:|
| Astra整回合 | 822.33 | 651.77 |
| 完整评价 | 468.42 | 878.41 |
| 内部测量 | 1.83 | 14.96 |
| Python动作墙钟 | 123.49 | 9.68 |
| 提交候选 | 134.05 | 0.15 |
| 工具往返及轮询等候 | 98.44 | 84.71 |

B最近8个候选完成间隔为1.96、1.90、5.56、6.30、4.09、3.99、3.68、3.40分钟，目前进入新诊断阶段；余12轮估计50–90分钟。C恢复后的4次完整评价总878秒、最近三个连续候选间隔5.67、6.31、5.67分钟；早停到恢复的36分钟空档不当作候选运行速度，余22轮估计2.5–4小时。诊断增加会改变区间，非承诺。v9无本轮实测，尚不给全部队列完成时刻。

##### 资源与计账

工作盘可用137.433GiB，较07:45约137.881GiB减少0.447GiB。B目录2.919GiB、C3.043GiB，较上次分别约+0.158/+0.284GiB；各低于12GiB，远高于全盘20GiB保留线。不需清理，无文件删除。08:09采样GPU0/1为0%/65%，08:10为0%/0%；两服务分别驻留约16.3/15.6GB，按Astra/CPU/生成阶段交替，不能由瞬时0%判为停止或声称全程满卡。

B搜索累计8891样本、2738945目标token、90.478 CPU秒；C23043样本、6081505目标token、36.166 CPU秒。B turn90研究者累计12233022 token，C turn50累计4361379 token，包含缓存输入；不是独立生成token或美元账单。B turn91后CPU累计105.125秒，见成功回执。两组工程各另计2212生成/2218前向，其中2080为吞吐校准，不计入30轮。恢复服务的额外实际模型加载已发生，各1次；不重跑W0。当前没有未决容量失败用量。全部原停止及负结果保留，旧Qwen/2B/8B/旧Gemma队列未恢复。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [C-broker-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/C-broker-launch.json) | {} | {"time_unix": "2026-11-05T23:41:30.222765+00:00"} |
| [C-controller-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/C-controller-launch.json) | {} | {"time_unix": "2026-11-05T23:42:07.201738+00:00"} |
| [C-controller-once.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/C-controller-once.json) | {} | {"time_unix": "2026-11-05T23:42:07.353625+00:00"} |
| [C-local-round4/conversation-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/C-local-round4/conversation-receipt.json) | {"status": "stopped_or_frozen"} | {} |
| [C-local-round4/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/C-local-round4/receipt.json) | {"status": "stopped_or_frozen"} | {} |
| [C-remote-round4/controller-status.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/C-remote-round4/controller-status.json) | {"stage": "finished"} | {"time_unix": "2026-11-05T23:21:16.449147+00:00"} |
| [C-resume-turn35/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/C-resume-turn35/receipt.json) | {} | {} |
| [C-resume-turn35/tool_result.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/C-resume-turn35/tool_result.json) | {} | {} |
| [C-stop-turn34/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/C-stop-turn34/receipt.json) | {} | {} |
| [C-stop-turn34/tool_result.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/C-stop-turn34/tool_result.json) | {} | {} |
| [heartbeat-0810/B-turn-0090/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/heartbeat-0810/B-turn-0090/receipt.json) | {} | {} |
| [heartbeat-0810/B-turn-0090/tool_result.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/heartbeat-0810/B-turn-0090/tool_result.json) | {} | {} |
| [heartbeat-0810/B-turn-0091/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/heartbeat-0810/B-turn-0091/receipt.json) | {} | {} |
| [heartbeat-0810/B-turn-0091/tool_result.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/heartbeat-0810/B-turn-0091/tool_result.json) | {} | {} |
| [heartbeat-0810/C-turn-0050/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06/heartbeat-0810/C-turn-0050/receipt.json) | {} | {} |

## 全部原始资产入口

本目录在固定提交下共有59个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/160-wsp-vlm-gemma3-C30-continuation-2026-11-06.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-C30-continuation-2026-11-06)。未复制模型权重、环境或凭据。
