# Branch B: mechanism investigation and static-weight repair

## Executive conclusion

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

## Scope and measurements

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

## Localization and competing explanations

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

## Controls that constrain the mechanism claim

### L34 direction decomposition and randomized controls

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

### L23/L32 dose tests

L32 column-619 attenuation and L23 column-3537 attenuation also changed the zebra margins,
but effects were contextual. The L32 half-ablation's evaluated zebra correction did not
repeat. Full L23 ablation repaired additional zero-count prompts but introduced three
total-count regressions. Enhancement controls repaired other cases, not the target zebra
failures. Correct-one controls and the wrong-three counterexample rule out a universal
one-suppression or spatial-repair interpretation.

Evidence: rounds 15–20, actions 0087/0089, 0094, 0098, 0104, 0108, and 0113.

### L24 head experiments

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

## Fixed pair tests

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

## Selected static edit and reproducibility

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

### Official changes and fresh audit

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

## Limits and next discriminating tests

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

## Complete development ledger

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
