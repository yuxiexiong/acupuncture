# Direct weight-repair experiment
## Plan
1. Diagnose 128 mixed practice problems with residual/MLP activation summaries; read concise failure excerpts.
2. Localize a specific failure mechanism using weights and teacher-forced good/bad continuations.
3. Test targeted interventions at multiple strengths; assess predicted behavior and paired accuracy.
4. Freeze a candidate before independent paired validation. Keep only a gain clearly larger than its paired standard error.
No training, gradient computation, model simulation, embedding/output/final-norm edits, or whole-tensor scaling.
Forward budget: 50; reserve at least 12 passes for independent confirmation and robustness.
## Current best
Unedited model; no evidence yet.

## Baseline pass 1
128 problems (64 GSM8K,64 MATH); accuracy 10.94% (GSM 17.19%, MATH 4.69%), mean length 30080.7 tokens, cutoff 90.62%; 114 failed by cutoff, zero finished wrong/no-answer. Main target: thinking-loop failure.

## Localization pass 2
Two teacher-forced math traces containing productive calculations and repetitions reproduced from failures. Attention induction mass (same relative next-token location +/-1 in previous clause): layer7 head5=.674; next candidates L19H5=.310, L15H7=.276, L23H5=.242. L7H5 puts .784 attention on previous repeated clause, only .013 locally. Weight statistics show no gross single-tensor anomaly. Test causal ablation of ONLY L7H5 via output-projection columns 1280:1536; not a global scale or termination intervention. Screening on 48 diagnostic problems, followed by dose-response and held-out validation.

Pass3: L7H5 ablation H=0 on paired 48: 4.17% vs 14.58%, delta -10.42 +/-6.13 pp; cutoff worsened 87.5%->95.83%. Reject causal claim that this early induction head drives looping. Pass4 matched TF measured sign; now test L7H5 gain=2 to test protective memory/comparison role. No candidate accepted.
