# 124．Qwen B两次搜索的覆盖复核

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-05；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

只用v8的50候选和v9前30候选，复核同一W0的144条错误被谁修好。

**实际过程、结果与后来更正**

两批分别至少修过38和12条，并集39；v9的12里11已在v8出现，只有一个新增覆盖且属于B1。并集是事后候选库统计，不是可部署组合补丁；没有实际叠加实验。

**来源身份**：`wsp-b-v8-v9-synthesis-2026-11-05`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：Branch B: mechanism investigation and static-weight repair

原路径：`experiments/wsp-b-v8-v9-synthesis-2026-11-05/v9-researcher-report-round30.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-b-v8-v9-synthesis-2026-11-05/v9-researcher-report-round30.md) · [单独阅读副本](../library/c179a0eeaa93b808.md)；SHA-256：`c179a0eeaa93b808bf1c338d1fc13f6ea5984d904c056fd5db4c4d175409159d`。

---

#### Branch B: mechanism investigation and static-weight repair

##### Executive conclusion

Thirty distinct static-weight candidates were fully evaluated on the same development set.
The harness-selected candidate is round 14, `c-37a38c134e5e044e609e621db2a8fab7e666bfe04dfdaecfe7340464a1333851`, a geometry-matched random-retention
control on decoder layer 34 MLP output column 1057. The official evaluation improves
accuracy from **320/464 (68.97%) to 322/464 (69.40%)**, with two corrections, no
correct-to-incorrect regressions, and one additional wrong-to-wrong answer change.
The repair score rises from **55/116 (0.474137931) to 56/116 (0.482758621)**.
The primary T0 joint score remains **27/58 (0.465517241)**.

These are small, selected, seen-development gains—not evidence of a general spatial-reasoning
repair. Both corrected zebra prompts repeated successfully in the final audit, but one
has a measured 0-versus-1 logit tie. The best candidate also has two evaluation/repeat
disagreements outside those corrections. The most defensible mechanistic conclusion is
that the investigated components affect **context-dependent competition among numerical
answers**. A shared spatial-success direction, a uniquely necessary zero-aligned component,
and a serial spatial circuit were not established.

Round 30 has the highest raw development accuracy, 325/464, but ties round 14 on the
repair score and was not selected by the harness. Automatic selection was preserved;
no alternative tie-breaking rule or post-diagnostic rescoring was introduced.

##### Scope and measurements

The public data are branch B, development split D: 58 image groups, each with eight
prompts spanning total/subset counting, T0/T1 wording, and B0/B1 prompting. B1 adds a
generic instruction to identify the reference and apply the spatial conditions.
The 464 prompts are not 464 independent observations. The repair metric uses 116 B0
total/subset pairs, still clustered within 58 image groups.

The model is Qwen3-VL with 36 decoder layers, hidden width 2560, MLP width 9728, and
32 attention output blocks of width 128. Investigations used complete generated answers,
selected digit logits, and captured activations. Captures at the last prompt token
measure a text-position state, not a visual token or an object-specific spatial variable.
Static weight interventions apply at every position, unlike temporary last-token probes.

The actual W0 evaluation, not the bundle's previous predictions, is the reference.
There were discrepancies between those sources and also between some evaluations and
fresh repeats. Input-token and rendered-chat hashes were checked. Array hashes, token
positions, and upstream invariance checks support implementation validity, but do not
remove numerical execution sensitivity.

All 30 candidates had zero recorded format errors and zero truncated outputs in their
full evaluations. No candidate lost more than one correct answer in any 58-prompt cell.
No held-out validation, branch-C evaluation, or generalization test was performed.

##### Localization and competing explanations

Initial same-image failure/success paraphrase contrasts did not support one shared
spatial-success direction: the contrasts mixed different numerical answer changes,
and early effects were strongly associated with prompt form. Removing two prompt-form
axes did not eliminate answer confounding. The resulting zero-success directions were
therefore treated as observational hypotheses, not identified spatial representations.

Component analysis nominated MLP output columns L23:3537, L32:619, L34:1057, and
attention output block L24:head13. L34 channel 1057 was strongly active on answer-one
examples, including correct-one controls, while a wrong-three/zero-gold strawberry
counterexample had little activity. Answer-free clarifications also failed to repair
most cases and damaged a correct dog-count response. These observations weaken a
simple spatial-condition-omission account.

Temporary removal of the L34 channel's last-token input changed the zebra 1-versus-0
margin from +0.5 to -0.25, but did not flip the harder tennis-ball or laptop failures.
The correct-one control also changed in margin without changing answer.
Static full-column removal reproduced the two zebra corrections. This supports a
local causal influence on numerical outputs; it does not identify what spatial
information, if any, the channel represents.

Relevant evidence: actions 0012–0019, 0022–0025, 0027–0029, and the fresh full-ablation
reference in actions 0153/0155.

##### Controls that constrain the mechanism claim

###### L34 direction decomposition and randomized controls

Removing only the zero-aligned projection of column 1057 did not produce the two zebra
corrections. Retaining that projection while removing its orthogonal component did.
Thus, removing the proposed zero-aligned component was not necessary for those observed
repairs. The latter intervention also increased the correct tennis-total one-versus-zero
margin, contradicting uniform suppression of answer one.

Transferring the edit to three other L34 channels gave no corresponding repairs, but
these controls were weak: global activity matching did not match their activity on the
critical answer-one cases. The conditional matching search found no eligible channels;
thresholds were not relaxed. Same-channel randomized-delta controls matched edit magnitude
but not the new column norm, so they also did not isolate direction cleanly.

Three geometry-matched random-retention controls matched the new-column norm and its
inner product with the original column before BF16 rounding. All three reproduced both
zebra corrections in their official evaluations. Round 14 is one of these controls.
This favors generic attenuation as a plausible explanation over a special role for
retaining the measured zero direction. It does not prove that every similarly sized
attenuation would behave identically.

Evidence: rounds 4–14, actions 0048–0050, the saved geometry-control plan, and round-14
provenance. The full ledger retains wrong-to-wrong changes and the unstable umbrella
corrections rather than counting all changed answers as mechanistic successes.

###### L23/L32 dose tests

L32 column-619 attenuation and L23 column-3537 attenuation also changed the zebra margins,
but effects were contextual. The L32 half-ablation's evaluated zebra correction did not
repeat. Full L23 ablation repaired additional zero-count prompts but introduced three
total-count regressions. Enhancement controls repaired other cases, not the target zebra
failures. Correct-one controls and the wrong-three counterexample rule out a universal
one-suppression or spatial-repair interpretation.

Evidence: rounds 15–20, actions 0087/0089, 0094, 0098, 0104, 0108, and 0113.

###### L24 head experiments

Head 13 attenuation repaired the two zebra prompts and some other development failures,
but full ablation also damaged a people-total answer. A preregistered head-24 control
was matched approximately on block/edit norm and diagnostic write magnitude; it did not
repair the two zebra targets, although it repaired other cases. This is evidence for a
relative difference between these two tested head interventions, not proof that head 13
uniquely implements spatial filtering. The control did not match every semantic or
activation property, and head edits were much larger than single-column MLP edits.

The complementary head-13 decomposition again matters: retaining the zero-aligned
projection while removing the orthogonal component preserved both zebra corrections.
The predicted direct change along that direction was nearly zero, whereas whole-layer
changes included subsequent MLP computation. Conversely, the projection-removal candidate
had evaluation/repeat disagreements on both zebra cases. Whole-layer residual changes
must not be equated with isolated head writes.

Evidence: rounds 21–27, actions 0115/0117, 0118, 0123, 0129, 0133, 0137, 0141,
0145/0147, and 0151; `L24_head_experiments_21_27.json`.

##### Fixed pair tests

The three final pairs were specified before their outcomes, independently reconstructed
from W0, and each zeroed exactly two MLP output columns (5120 changed scalars).
They were not added cumulatively to head edits.

- **L23+L32, round 28:** 323/464, six corrections and three regressions. Two corrected
  zebra prompt variants were additional to the union of the single-edit corrections.
- **L23+L34, round 29:** 322/464, five corrections and the same three total-count
  regressions. One additional zebra prompt variant was corrected.
- **L32+L34, round 30:** 325/464, five corrections and no regressions. Tennis-ball B1 and
  laptop B1 corrections were additional to the single-edit union. The umbrella correction
  is not secure causal evidence because W0 itself repeats as the correct answer.

All three fixed 13-prompt diagnostic panels matched their respective evaluated complete
answers, with no truncation, and passed the planned ordering checks. This does not cover
every changed prompt outside those panels.

Margin interaction was defined as m_pair - m_first - m_second + m_W0. Results included
small nonadditivities. For example, in round 29, the incremental L34 one-versus-zero effect
was smaller after L23 ablation on the two zebra cases; on the correct tennis-total control,
the standalone L34 effect was +0.5 but the conditional effect was -0.25. BF16 resolution
and near ties matter. Zero interactions in some pre-output activations follow from causal
ordering of output-column edits; they do not prove independence.

Overlapping repairs, changed downstream activity, and pair nonadditivity do not establish
serial mediation. No path-specific restoration, edge intervention, or causal mediation
experiment isolated such a route. Evidence: actions 0157/0158/0160, 0164/0165/0166,
0170/0171/0172, and the three pair-diagnostic audit files.

##### Selected static edit and reproducibility

Base: `w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06`.

Selected candidate: `c-37a38c134e5e044e609e621db2a8fab7e666bfe04dfdaecfe7340464a1333851`.

Only `model.language_model.layers.34.mlp.down_proj.weight[:,1057]` differs from W0.
For original column w, let q=w/||w||. Let w5 be the retained-projection column from
round 5, alpha=q^T w5, and beta=sqrt(||w5||^2-alpha^2). The new column is
BF16_RNE(alpha*q + beta*v), with unit v orthogonal to q drawn using the fixed seed
105706. All other scalars are W0; the registry parent is not a cumulative edit recipe.

Effective changed scalars: **2559**.
Delta L2: **1.174356407261**.
Maximum absolute scalar change: **0.185745239258**.
Effective tensor content SHA256:
`221a5c841306393dde3a5f07319c3534c398b798e594e830e9fdd1907cf1b57b`.

See commit action 0078, evaluation 0079, `round14_provenance.json`, and
`geometry_control_plan.json`. The ledger includes all candidate IDs, commit manifests,
evaluation action IDs, cell counts, and complete changed-answer lists.

###### Official changes and fresh audit

The two official corrections are:
- `B-10840:subset:T1:B0`, zebra farther than giraffe: 1 -> 0, gold 0.
- `B-3805:subset:T1:B1`, zebra left of duck: 1 -> 0, gold 0.

Both repeated as 0 in action 0173, while fresh W0 repeated as 1 in action 0174.
Their measured one-versus-zero margins changed from +0.5 to 0.0 and from +0.25 to
-0.25, respectively. The first remains a tie-sensitive result, not a robust-margin claim.
All five tested upstream tensors matched W0 on all 15 prompts.

The additional official wrong-to-wrong change, `B-188190:subset:T0:B0` (gold 4),
was 1 -> 2 in evaluation but repeated as 1; its measured one-versus-two margin was tied.
The umbrella control `B-518494:total:T1:B0` was 4 for both W0 and the selected candidate
in evaluation, but both freshly repeated as 3, with tied three/four logits.
Thus 13/15 selected-candidate repeats matched evaluation, and 14/15 W0 repeats matched.
Official scores were not replaced with diagnostic scores.

The other documented instability cases include the L32 half-ablation zebra result
(actions 0087/0089) and the L24 projection-removal zebra results (0145/0147). Identical
prompt hashes and repeated capture hashes do not establish why evaluation and diagnostic
execution differed. No unsupported backend explanation is asserted.

##### Limits and next discriminating tests

1. All localization, candidate design, evaluation, and selection used development data.
   Thirty adaptive candidates and repeated prompt variants preclude an unqualified
   generalization or statistical-significance claim.
2. The selected gain is two prompts on two seen zebra images; the B0 repair metric gains
   only one paired success. Primary T0 joint performance does not improve.
3. Several effects occur at BF16 ties or very small margins. The fresh diagnostic audit
   was limited to 15 selected-candidate prompts, not a fresh full-development evaluation.
4. The components are answer-confounded and affect correct counting as well as failures.
   Negative controls were imperfect and some predeclared predictions failed.
5. Static output edits do not isolate spatial information flow. No unique spatial circuit,
   path mediation, or broad ability restoration is claimed.

The appropriate next tests would use untouched image groups with balanced answer counts,
matched relation/reference counterfactuals, execution-matched repeat audits, and
path-specific restoration of candidate downstream signals. These are proposals, not
completed experiments, and no additional candidate was created after round 30.

##### Complete development ledger

Corrections and regressions below are relative to the official W0 evaluation.
They are descriptive counts, not independent causal successes; in particular,
some corrections include the unstable umbrella case.

| Round | Intervention | Correct / 464 | Corrections | Regressions | Repair score | Changed scalars | Delta L2 |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | L34 c1057 zero | 323 | 3 | 0 | 0.482758621 | 2560 | 1.179982456 |
| 2 | L34 c1057 half | 323 | 3 | 0 | 0.482758621 | 2560 | 0.589991228 |
| 3 | L34 c1057 enhance | 321 | 1 | 0 | 0.474137931 | 2560 | 0.590172814 |
| 4 | L34 remove parallel | 321 | 1 | 0 | 0.474137931 | 2517 | 0.115027721 |
| 5 | L34 retain parallel | 323 | 3 | 0 | 0.482758621 | 2559 | 1.174356533 |
| 6 | L34 transfer c2020 | 320 | 0 | 0 | 0.474137931 | 2552 | 1.174326091 |
| 7 | L34 transfer c2277 | 320 | 0 | 0 | 0.474137931 | 2553 | 1.174287063 |
| 8 | L34 transfer c2958 | 319 | 0 | 1 | 0.465517241 | 2553 | 1.174480080 |
| 9 | L34 random delta seed105701 | 320 | 0 | 0 | 0.474137931 | 2559 | 1.174524690 |
| 10 | L34 random delta seed105702 | 322 | 2 | 0 | 0.482758621 | 2559 | 1.174387434 |
| 11 | L34 random delta seed105703 | 321 | 1 | 0 | 0.474137931 | 2559 | 1.174414635 |
| 12 | L34 geometry control seed105704 | 323 | 3 | 0 | 0.482758621 | 2560 | 1.174350122 |
| 13 | L34 geometry control seed105705 | 323 | 3 | 0 | 0.482758621 | 2560 | 1.174355339 |
| 14 (selected) | L34 geometry control seed105706 | 322 | 2 | 0 | 0.482758621 | 2559 | 1.174356407 |
| 15 | L32 c619 half | 323 | 3 | 0 | 0.482758621 | 2560 | 0.544594545 |
| 16 | L32 c619 zero | 323 | 3 | 0 | 0.482758621 | 2560 | 1.089189089 |
| 17 | L32 c619 enhance | 321 | 1 | 0 | 0.474137931 | 2560 | 0.544661564 |
| 18 | L23 c3537 half | 322 | 3 | 1 | 0.474137931 | 2560 | 0.582150555 |
| 19 | L23 c3537 zero | 321 | 4 | 3 | 0.474137931 | 2560 | 1.164301109 |
| 20 | L23 c3537 enhance | 322 | 2 | 0 | 0.474137931 | 2560 | 0.581959456 |
| 21 | L24 head13 half | 322 | 3 | 1 | 0.482758621 | 327680 | 5.402974948 |
| 22 | L24 head13 zero | 324 | 5 | 1 | 0.482758621 | 327680 | 10.805949896 |
| 23 | L24 head13 enhance | 324 | 4 | 0 | 0.482758621 | 327680 | 5.402868355 |
| 24 | L24 head24 matched-half control | 321 | 1 | 0 | 0.474137931 | 327680 | 5.403301415 |
| 25 | L24 head24 matched-full control | 322 | 2 | 0 | 0.482758621 | 327680 | 10.806057120 |
| 26 | L24 head13 remove parallel | 322 | 2 | 0 | 0.482758621 | 277277 | 0.351931252 |
| 27 | L24 head13 retain parallel | 323 | 4 | 1 | 0.482758621 | 327669 | 10.800232462 |
| 28 | L23 c3537 + L32 c619 zero | 323 | 6 | 3 | 0.474137931 | 5120 | 1.594343108 |
| 29 | L23 c3537 + L34 c1057 zero | 322 | 5 | 3 | 0.474137931 | 5120 | 1.657695892 |
| 30 | L32 c619 + L34 c1057 zero | 325 | 5 | 0 | 0.482758621 | 5120 | 1.605830461 |

---

### 原件 2：B两次搜索合看：高度重叠的修复、一个新增覆盖与选择规则的边界

原路径：`experiments/wsp-b-v8-v9-synthesis-2026-11-05/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-b-v8-v9-synthesis-2026-11-05/REPORT.zh-CN.md) · [单独阅读副本](../library/6c31d93603fdebcd.md)；SHA-256：`6c31d93603fdebcdf753927d54e510dab82c56ae2adee07c26a84baab60f4493`。

---

#### B两次搜索合看：高度重叠的修复、一个新增覆盖与选择规则的边界

##### Material Passport

2026-11-05；academic-research-suite validate；Verification Status: ANALYZED。本次仅CPU复算已保存回答与读取研究者记录，0新增模型调用、0GPU实验，无补丁叠加、无改动B/C运行。第一轮指v8全部50候选；第二轮指v9已完成的前30候选，不是尚未完成的50轮接续。读取时v8已冻结，v9仍在正式机制报告/冻结收尾；本文不把它误称为完整50轮结束。

58个相同开发来源组、464条相关输入。逐份核验v9返回的W0与v8的输入ID、标签、解析答案和正确性完全一致；80候选的主分数及准确率全部CPU复算一致。未作模型重放或独立验证；58组是来源单位，116问法配对与464输入不是独立样本。

##### 主要结论

最有根据的综合收益不是“两份最佳补丁互补很多”，而是发现粗调与细调高度重合的行为覆盖，并用第二轮控制实验削弱“已找到特定空间失败方向”的解释。存在一个值得保留的新增覆盖案例，但不足以支持大量协同收益；跨版本权重组合从未执行。

| 已保存输出中的覆盖 | v8 50候选 | v9 30候选 | 两批并集 |
|---|---:|---:|---:|
| W0的144条错误中至少一次修对 | 38 | 12 | 39 |
| W0错误中从未修对 | 106 | 132 | 105 |
| 至少被修对的总数题 / 子集题 | 19 / 19 | 2 / 10 | 19 / 20 |
| 含W0、事后挑选整对输出能覆盖的B0联合正确配对 | 68/116 | 57/116 | 68/116 |

v9修过的12条错误有11条已被v8修过。两批80候选并集仍有105/144（72.92%）原错误没有修对。此处“并集”使用真实答案事后挑选，是已有候选库覆盖统计，不是可部署补丁、合成模型分数或未来方法上限；不允许从不同候选分别挑总数和子集再伪造同候选联合正确。

##### 1. 两个自动最佳没有新增修复互补

v8最佳第50轮：主分数61/116=52.59%，全输入324/464=69.83%，13修复、9损伤。
v9最佳第14轮：主分数56/116=48.28%，全输入322/464=69.40%，2修复、0损伤。

v9最佳修复的两条均已被v8最佳修复：`B-10840:subset:T1:B0`、`B-3805:subset:T1:B1`，都是斑马条件计数1→0。两者修复集合没有新增互补。v9在v8损伤题上仍正确不等于它可以抵消叠加后的损伤：W0本来就答对这些题，而且我们没有把v9补丁加到v8背景上测试。

##### 2. 唯一新增覆盖是真实线索，但范围非常小

`B-538866:subset:T0:B1`，标签0、W0答1。v8的50个候选全部仍答1；v9第19、22、28、29、30轮答0。这条是旧版87条“预测数字从未变化”的原错误之一。

说明：细化操作至少能改变粗调族未改变的一条输出；不能由此推断独立空间机制或新模型有效。五个候选共享同一开发输入和相关选择历史，不是五次独立复现。这条属于加强提示B1，而主修复指标按普通提示B0计算，所以没有增加主指标覆盖。第30轮的固定13条重复诊断名单没有包含这一B1输入，不能借那份重复检查给该新增修复背书。

##### 3. 更值得比较的是两个非最终赢家，但互补仍只有一条

| 候选 | 修复 / 损伤 | 主分数 | 全输入正确 |
|---|---:|---:|---:|
| v8第47轮 | 13 / 0 | 59/116=50.86% | 333/464=71.77% |
| v9第30轮 | 5 / 0 | 56/116=48.28% | 325/464=70.04% |

两者修复交集4条，已有修复并集14条，新增互补仅上述B1输入；整对输出的主指标覆盖仍是59/116。并集14不是预测实际权重组合会修对14条，组合可能相互抵消、产生新效果或新增损伤。

两个选择边界不同：v8第50轮按主指标胜过第47轮，但全输入净少9条正确；v9第30轮比第14轮多修对3条且无损伤，但主指标相同、实际改动5120标量多于第14轮2559标量，因此未被固定规则选中。不能事后更改赢家或主指标，但解释研究时必须保留这些非赢家候选，避免只比较两个best而遗漏局部互补和成本取舍。

##### 4. 两次结果合起来更支持什么解释

已测行为：v8最终补丁的13修复与9损伤全部伴随数字下降；但第47轮有3条向上修复，所以不是所有粗调都只压低数字。v9选中补丁的两条修复也是1→0。不同参数位置影响了高度重叠的少量错误。

v9控制与重复记录进一步显示：L34:1057的三个几何匹配随机保留方向都复现两条斑马修复；保留原提议的零相关投影也能修复，删除该投影并非必要。部分正确计数也受影响，若干例子处于logit近零/相等边界，官方批量评价与诊断重复出现差异。研究者报告把可支持结论限制为“这些组件影响依赖上下文的数字答案竞争”，不声称找到了通用空间成功方向、唯一通道或串行空间回路。

综合推断：两版可能反复碰到了同一小群容易翻转的回答，而未普遍修复空间关系计算。这是由覆盖重合与v9控制共同支持的工作解释，仍不能确定v8是否通过v9定位的通道起作用；两个不同干预产生同样回答，不证明内部路径相同。上游norm校准影响后续通道活动，是可检验但本次未测的联系，不能写成已知链条。

另一方面，v9内部已有双列组合产生单列修复并集之外的修复，提示非线性组合并非没有可能。因此，“两个最佳的修复集合重叠”不能证明实际叠加必然无效。可说的是目前缺乏期待大幅收益的直接证据，跨版本组合的符号和大小未知。

##### 5. 本次能交付的收获

- 一份跨80候选的逐题覆盖账，识别共同105条未修复错误，防止把更多同类搜索当作覆盖已扩大。
- 一个粗调始终不变、细调能翻转的明确输入，连同B1限定和重复检查缺口。
- 两组非赢家的有限互补与选择规则取舍，说明最终分数不足以总结整个搜索。
- 更受约束的机制解释：局部数值决策影响有证据，特定空间失败机制未建立。

本次不新增实验，也不把方向建议升级为执行计划。若以后研究跨版本组合，需要另行说明它要验证哪条联系；不能以本次答案并集代替组合测量。

##### 核验、自查与边界

脚本analyze.py验证80份结果的输入唯一性、固定标签、正确性、116联合配对和准确率，并核对跨版本W0一致。输出analysis.json包括具体输入ID、逐轮结果和原始回执SHA256；v9-scored-evidence.json.gz只摘取已存评分及源hash；v8复用既有evidence.json.gz。v9-researcher-report-round30.md为读取时已有报告草稿，SHA256 c179a0eeaa93b808bf1c338d1fc13f6ea5984d904c056fd5db4c4d175409159d；它的科学解释仍由原动作证据限定，不以自述替代验证。

C01–C04：通过，问题保持内部修补，复用两次搜索且保留弱增益、随机对照与损伤；C05–C07：不涉及新增干预，未拼接权重、路径或跨版本状态；C08–C10：通过，并集/主指标/全输入分开，不把相同答案当同一机制；C11–C12：通过，失败和不稳定保留、0新模型调用；C13：通过，开发选择身份、来源hash和阶段完成状态明确；C14：通过，允许有限或负面综合收益，不自动加实验。相关E03/E10/E12/E16/E20/E22/E23/E25按扰动非坐标数、完整回答、控制边界、负面保留、不强行单因、开发非确认、算术非重放与不扩范围处理。反方：修复集合重合不能排除非线性协同；同一方向也可能由正确视觉证据产生；全50与前30搜索预算不同，不能作为细调普遍劣于粗调的受控比较；新增一题并非独立泛化。自查由同一助手执行。

统计谬误11/11检查：展示分层与个体ID；不以聚合推断单题因果；D筛选限制外推；无事后协变量控制；报告144原错误基率；同W0但非独立验证；全80候选不丢失败；明确多重选择；保留事后分析身份；相同输出不等于相同路径；不反推通道天然功能。未报告确认性p值、置信区间或“显著”结论。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| 本目录未提取到上述类型JSON | 不据此推断运行成功或失败 | — |

## 全部原始资产入口

本目录在固定提交下共有6个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/124-wsp-b-v8-v9-synthesis-2026-11-05.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-b-v8-v9-synthesis-2026-11-05)。未复制模型权重、环境或凭据。
